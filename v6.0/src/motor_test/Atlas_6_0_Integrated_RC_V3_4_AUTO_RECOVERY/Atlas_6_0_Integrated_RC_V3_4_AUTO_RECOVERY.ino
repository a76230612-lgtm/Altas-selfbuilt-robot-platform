/*
  Atlas 6.0 - Integrated Release Candidate V3.4 AUTO RECOVERY
  Controller: ESP32 DEVKIT V1

  Proven Stage 8C pin map + Servo on GPIO21.

  L298N:
    ENA=13 IN1=14 IN2=4
    ENB=33 IN3=32 IN4=23
  Encoders:
    LEFT A=25 B=26
    RIGHT A=18 B=19
  US-100:
    TRIG=27 ECHO=34 VCC=3V3 GND=GND
  Servo:
    SIGNAL=21 VCC=5V GND=GND

  Distance policy:
    <10cm      BLOCKED
    10-<15cm   CAUTION
    >=15cm     CLEAR
    invalid    UNKNOWN

  Continuous scan:
    LEFT(5) -> CENTER(90) -> RIGHT(175) -> CENTER(90) -> repeat

  Boot state:
    DISARMED / AUTO OFF / US_ONLY / SWEEP ON

  Wi-Fi AP:
    SSID ATLAS_6_0
    PASS atlas6000
    TCP  8888

  Commands (Serial or TCP):
    HELP
    PING
    STATUS
    ARM
    DISARM
    STOP
    HB or HEARTBEAT
    AUTO,ON / AUTO,OFF
    MODE,US_ONLY / MODE,FUSION
    SWEEP,ON / SWEEP,OFF
    PWM,<0..255>
    FWD / BACK / LEFT / RIGHT
    CAM,EDGE,SAFE|EDGE|UNKNOWN
    CAM,LEFT,FREE|BLOCKED|UNKNOWN
    CAM,RIGHT,FREE|BLOCKED|UNKNOWN

  Stage 10 aliases are accepted:
    CMD,STATUS
    CMD,ARM
    CMD,DISARM
    CMD,STOP
    CMD,HEARTBEAT

  Safety:
    - reboot -> DISARMED
    - network heartbeat timeout 350ms -> STOP + DISARM
    - controlled network disconnect -> STOP + DISARM
    - FUSION mode requires fresh Camera EDGE=SAFE
    - CENTER UNKNOWN/stale -> STOP
    - US-100 has physical veto authority

  First integrated test: wheels OFF the table.
*/

#include <Arduino.h>
#include <WiFi.h>
#include <esp_arduino_version.h>

// ---------------- Pins ----------------
static const uint8_t L_EN=13, L_IN1=14, L_IN2=4;
static const uint8_t R_EN=33, R_IN1=32, R_IN2=23;
static const uint8_t ENC_L_A=25, ENC_L_B=26;
static const uint8_t ENC_R_A=18, ENC_R_B=19;
static const uint8_t US_TRIG=27, US_ECHO=34;
static const uint8_t SERVO_PIN=21;

// ---------------- Wi-Fi ----------------
static const char* AP_SSID="ATLAS_6_0";
static const char* AP_PASS="atlas6000";
static const uint16_t TCP_PORT=8888;
WiFiServer server(TCP_PORT);
WiFiClient client;

// ---------------- PWM compatibility ----------------
static const uint8_t CH_L=0, CH_R=1, CH_SERVO=2;

bool pwmAttachCompat(uint8_t pin,uint8_t channel,uint32_t freq,uint8_t bits){
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  (void)channel;
  return ledcAttach(pin,freq,bits);
#else
  double actual=ledcSetup(channel,freq,bits);
  if(actual<=0) return false;
  ledcAttachPin(pin,channel);
  return true;
#endif
}

void pwmWriteCompat(uint8_t pin,uint8_t channel,uint32_t duty){
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  (void)channel;
  ledcWrite(pin,duty);
#else
  (void)pin;
  ledcWrite(channel,duty);
#endif
}

// ---------------- Motor ----------------
static const uint32_t MOTOR_FREQ=5000;
static const uint8_t MOTOR_BITS=8;
static const bool LEFT_INVERTED=false;
static const bool RIGHT_INVERTED=true;
static const int DEFAULT_DRIVE_PWM=100;
static const int DEFAULT_TURN_PWM=100;
static const uint32_t TURN_PULSE_MS=300;

// Startup boost: briefly overcome static friction, then fall back to cruise PWM.
static const int STARTUP_BOOST_PWM=220;
static const uint32_t STARTUP_BOOST_MS=150;

// Recovery backoff:
// Total reverse time is approximately STARTUP_BOOST_MS + BACKOFF_AFTER_BOOST_MS.
// Keep it short because Atlas 6.0 has no rear obstacle sensor.
static const int BACKOFF_CRUISE_PWM=80;
static const uint32_t BACKOFF_AFTER_BOOST_MS=120;

int drivePwm=DEFAULT_DRIVE_PWM;

// ---------------- Encoder ----------------
volatile long encL=0,encR=0;
static const float LEFT_PPR=632.05f;
static const float RIGHT_PPR=634.17f;
static const float WHEEL_CIRC_CM=21.40f;

void IRAM_ATTR isrL(){
  bool a=digitalRead(ENC_L_A), b=digitalRead(ENC_L_B);
  encL+=(a==b)?1:-1;
}
void IRAM_ATTR isrR(){
  bool a=digitalRead(ENC_R_A), b=digitalRead(ENC_R_B);
  encR+=(a==b)?1:-1;
}

// ---------------- US-100 ----------------
static const float BLOCKED_CM=10.0f;
static const float CAUTION_CM=15.0f;
static const uint32_t ECHO_TIMEOUT_US=25000UL;
static const uint8_t US_N=3;
static const uint8_t US_MIN_VALID=2;
static const uint32_t US_GAP_MS=35;
static const uint32_t CENTER_STALE_MS=1200;
static const uint32_t SIDE_STALE_MS=2200;

static const uint8_t RG_UNKNOWN=0;
static const uint8_t RG_BLOCKED=1;
static const uint8_t RG_CAUTION=2;
static const uint8_t RG_CLEAR=3;
float distL=NAN,distC=NAN,distR=NAN;
uint8_t rangeL=RG_UNKNOWN,rangeC=RG_UNKNOWN,rangeR=RG_UNKNOWN;
uint32_t distLms=0,distCms=0,distRms=0;

// ---------------- Servo ----------------
static const uint32_t SERVO_FREQ=50;
static const uint8_t SERVO_BITS=16;
static const uint32_t SERVO_MAX_DUTY=(1UL<<SERVO_BITS)-1UL;
static const uint16_t SERVO_MIN_US=1000;
static const uint16_t SERVO_MAX_US=2000;

// Near-full 180-degree field, without continuously hitting hard end stops.
static const int ANG_LEFT=5;
static const int ANG_CENTER=90;
static const int ANG_RIGHT=175;

// Set true only if physical left/right are reversed after your mechanical change.
static const bool SERVO_REVERSED=false;
static const uint32_t SERVO_SETTLE_MS=220;

static const uint8_t POS_LEFT=0;
static const uint8_t POS_CENTER_A=1;
static const uint8_t POS_RIGHT=2;
static const uint8_t POS_CENTER_B=3;
uint8_t scanPos=POS_CENTER_A;
bool sweepOn=true;
// Keep Serial readable while the servo continues scanning.
bool scanLogOn=false;
bool servoWaiting=false;
uint32_t servoMoveMs=0;

// ---------------- Camera ----------------
static const uint8_t CE_UNKNOWN=0;
static const uint8_t CE_SAFE=1;
static const uint8_t CE_EDGE=2;
static const uint8_t CS_UNKNOWN=0;
static const uint8_t CS_FREE=1;
static const uint8_t CS_BLOCKED=2;
uint8_t camEdge=CE_UNKNOWN;
uint8_t camL=CS_UNKNOWN,camR=CS_UNKNOWN;
uint32_t cameraMs=0;
static const uint32_t CAMERA_STALE_MS=1200;

// ---------------- Robot state ----------------
static const uint8_t US_ONLY=0;
static const uint8_t FUSION=1;
static const uint8_t STOPPED=0;
static const uint8_t FORWARD=1;
static const uint8_t BACKWARD=2;
static const uint8_t TURN_LEFT=3;
static const uint8_t TURN_RIGHT=4;
uint8_t mode=US_ONLY;
uint8_t motion=STOPPED;
bool armed=false;
bool autoOn=false;
uint32_t turnUntilMs=0;
int previousTurn=0; // -1 left, +1 right
uint32_t lastNoPathMsgMs=0;

// Recovery state machine.
// EDGE: one short reverse, then wait for Camera SAFE, scan sides, turn.
// WALL BLOCKED: one short reverse, scan sides, turn.
// UNKNOWN camera state never triggers reverse; it only STOPs.
static const uint8_t REC_NONE=0;
static const uint8_t REC_BACKOFF=1;
static const uint8_t REC_WAIT_TURN=2;

static const uint8_t REC_CAUSE_NONE=0;
static const uint8_t REC_CAUSE_EDGE=1;
static const uint8_t REC_CAUSE_WALL=2;

uint8_t recoveryState=REC_NONE;
uint8_t recoveryCause=REC_CAUSE_NONE;
uint32_t recoveryUntilMs=0;
uint32_t lastRecoveryNoPathMsgMs=0;

// ---------------- Network safety ----------------
static const uint32_t HB_TIMEOUT_MS=350;
uint32_t lastNetMs=0;
bool hadClient=false;
bool networkControl=false;

// ---------------- Input buffers ----------------
String serialBuf,netBuf;
uint32_t serialLastByteMs=0,netLastByteMs=0;
static const uint32_t COMMAND_IDLE_FLUSH_MS=40;

// ---------------- Helpers ----------------
const char* rangeName(uint8_t s){
  if(s==RG_BLOCKED)return "BLOCKED";
  if(s==RG_CAUTION)return "CAUTION";
  if(s==RG_CLEAR)return "CLEAR";
  return "UNKNOWN";
}
const char* motionName(uint8_t s){
  if(s==FORWARD)return "FORWARD";
  if(s==BACKWARD)return "BACKWARD";
  if(s==TURN_LEFT)return "TURN_LEFT";
  if(s==TURN_RIGHT)return "TURN_RIGHT";
  return "STOPPED";
}
const char* modeName(){return mode==FUSION?"FUSION":"US_ONLY";}
const char* recoveryName(){
  if(recoveryState==REC_BACKOFF)return "BACKOFF";
  if(recoveryState==REC_WAIT_TURN)return "WAIT_TURN";
  return "IDLE";
}
const char* camEdgeName(){
  if(camEdge==CE_SAFE)return "SAFE";
  if(camEdge==CE_EDGE)return "EDGE";
  return "UNKNOWN";
}
const char* camSideName(uint8_t s){
  if(s==CS_FREE)return "FREE";
  if(s==CS_BLOCKED)return "BLOCKED";
  return "UNKNOWN";
}

void sendLine(const String& s){
  Serial.println(s);
  if(client&&client.connected()) client.println(s);
}

// ---------------- Motor functions ----------------
void oneMotor(uint8_t en,uint8_t ch,uint8_t in1,uint8_t in2,int value,bool inverted){
  value=constrain(value,-255,255);
  if(inverted)value=-value;
  if(value==0){
    digitalWrite(in1,LOW);digitalWrite(in2,LOW);
    pwmWriteCompat(en,ch,0);return;
  }
  bool f=value>0;int p=abs(value);
  digitalWrite(in1,f?HIGH:LOW);
  digitalWrite(in2,f?LOW:HIGH);
  pwmWriteCompat(en,ch,p);
}
void drive(int l,int r){
  oneMotor(L_EN,CH_L,L_IN1,L_IN2,l,LEFT_INVERTED);
  oneMotor(R_EN,CH_R,R_IN1,R_IN2,r,RIGHT_INVERTED);
}

// Apply a short high-torque kick only when starting from a full stop.
// This solves the observed condition: motor buzzes at low PWM but runs once already moving.
void driveWithStartupBoost(int runL,int runR){
  int boostL=0;
  int boostR=0;

  if(runL>0)boostL=STARTUP_BOOST_PWM;
  else if(runL<0)boostL=-STARTUP_BOOST_PWM;

  if(runR>0)boostR=STARTUP_BOOST_PWM;
  else if(runR<0)boostR=-STARTUP_BOOST_PWM;

  drive(boostL,boostR);
  delay(STARTUP_BOOST_MS);
  drive(runL,runR);
}
void stopRobot(const char* reason){
  drive(0,0);motion=STOPPED;turnUntilMs=0;
  if(reason){String s="MOTION,STOP,REASON,";s+=reason;sendLine(s);}
}
void invalidateRangesAfterTurn(){
  distLms=distCms=distRms=0;
  rangeL=rangeC=rangeR=RG_UNKNOWN;
}
void startLeftTurn(){
  if(!armed)return;
  if(motion==STOPPED)driveWithStartupBoost(-DEFAULT_TURN_PWM,DEFAULT_TURN_PWM);
  else drive(-DEFAULT_TURN_PWM,DEFAULT_TURN_PWM);
  motion=TURN_LEFT;turnUntilMs=millis()+TURN_PULSE_MS;previousTurn=-1;
  sendLine("AUTO,ACTION,TURN_LEFT");
}
void startRightTurn(){
  if(!armed)return;
  if(motion==STOPPED)driveWithStartupBoost(DEFAULT_TURN_PWM,-DEFAULT_TURN_PWM);
  else drive(DEFAULT_TURN_PWM,-DEFAULT_TURN_PWM);
  motion=TURN_RIGHT;turnUntilMs=millis()+TURN_PULSE_MS;previousTurn=1;
  sendLine("AUTO,ACTION,TURN_RIGHT");
}

void clearRecovery(){
  recoveryState=REC_NONE;
  recoveryCause=REC_CAUSE_NONE;
  recoveryUntilMs=0;
}

void startRecovery(uint8_t cause,const char* stopReason,const char* actionName){
  if(recoveryState!=REC_NONE)return;
  if(!armed||!autoOn)return;

  // Stop first. Then reverse for a tightly bounded interval.
  stopRobot(stopReason);

  driveWithStartupBoost(-BACKOFF_CRUISE_PWM,-BACKOFF_CRUISE_PWM);
  motion=BACKWARD;

  recoveryState=REC_BACKOFF;
  recoveryCause=cause;
  recoveryUntilMs=millis()+BACKOFF_AFTER_BOOST_MS;

  String s="AUTO,ACTION,BACKOFF,CAUSE,";
  s+=actionName;
  sendLine(s);
}

bool serviceRecovery(){
  if(recoveryState==REC_NONE)return false;

  if(!armed||!autoOn){
    stopRobot(nullptr);
    clearRecovery();
    return true;
  }

  if(recoveryState==REC_BACKOFF){
    if((int32_t)(millis()-recoveryUntilMs)>=0){
      stopRobot(nullptr);

      // Old geometry is invalid after moving backward.
      invalidateRangesAfterTurn();
      scanPos=POS_CENTER_A;
      servoWaiting=false;

      recoveryState=REC_WAIT_TURN;
      sendLine("AUTO,ACTION,BACKOFF_DONE,WAITING_FOR_TURN");
    }
    return true;
  }

  if(recoveryState==REC_WAIT_TURN){
    // For a cliff/edge recovery, do not turn or move forward until
    // the strict camera safety gate has returned to SAFE.
    if(recoveryCause==REC_CAUSE_EDGE && !cameraGate()){
      return true;
    }

    int d=chooseTurn();

    if(d<0){
      clearRecovery();
      startLeftTurn();
      return true;
    }

    if(d>0){
      clearRecovery();
      startRightTurn();
      return true;
    }

    if(millis()-lastRecoveryNoPathMsgMs>800){
      lastRecoveryNoPathMsgMs=millis();
      sendLine("AUTO,ACTION,RECOVERY_NO_SAFE_TURN");
    }

    return true;
  }

  clearRecovery();
  return false;
}

// ---------------- Servo functions ----------------
uint16_t angleToPulse(int logical){
  logical=constrain(logical,0,180);
  int physical=SERVO_REVERSED?(180-logical):logical;
  return (uint16_t)map(physical,0,180,SERVO_MIN_US,SERVO_MAX_US);
}
uint32_t pulseToDuty(uint16_t pulseUs){
  const uint32_t periodUs=1000000UL/SERVO_FREQ;
  return (uint32_t)((uint64_t)pulseUs*SERVO_MAX_DUTY/periodUs);
}
void servoAngle(int logical){
  pwmWriteCompat(SERVO_PIN,CH_SERVO,pulseToDuty(angleToPulse(logical)));
  servoWaiting=true;servoMoveMs=millis();
}
int scanAngle(uint8_t p){
  if(p==POS_LEFT)return ANG_LEFT;
  if(p==POS_RIGHT)return ANG_RIGHT;
  return ANG_CENTER;
}
const char* scanName(uint8_t p){
  if(p==POS_LEFT)return "LEFT";
  if(p==POS_RIGHT)return "RIGHT";
  return "CENTER";
}
void nextScan(){
  if(scanPos==POS_LEFT)scanPos=POS_CENTER_A;
  else if(scanPos==POS_CENTER_A)scanPos=POS_RIGHT;
  else if(scanPos==POS_RIGHT)scanPos=POS_CENTER_B;
  else scanPos=POS_LEFT;
  servoAngle(scanAngle(scanPos));
}

// ---------------- US functions ----------------
float readUsOnce(){
  digitalWrite(US_TRIG,LOW);delayMicroseconds(3);
  digitalWrite(US_TRIG,HIGH);delayMicroseconds(10);digitalWrite(US_TRIG,LOW);
  uint32_t us=pulseIn(US_ECHO,HIGH,ECHO_TIMEOUT_US);
  if(!us)return NAN;
  float cm=us*0.0343f/2.0f;
  if(cm<2.0f||cm>400.0f)return NAN;
  return cm;
}
void sortSmall(float* a,uint8_t n){
  for(uint8_t i=0;i<n;i++)for(uint8_t j=i+1;j<n;j++)if(a[j]<a[i]){float t=a[i];a[i]=a[j];a[j]=t;}
}
float readUsMedian(){
  float v[US_N];uint8_t n=0;
  for(uint8_t i=0;i<US_N;i++){
    float cm=readUsOnce();if(!isnan(cm))v[n++]=cm;
    if(i+1<US_N)delay(US_GAP_MS);
  }
  if(n<US_MIN_VALID)return NAN;
  sortSmall(v,n);
  return (n%2)?v[n/2]:(v[n/2-1]+v[n/2])/2.0f;
}
uint8_t classify(float cm){
  if(isnan(cm))return RG_UNKNOWN;
  if(cm<10.0f)return RG_BLOCKED;
  if(cm<15.0f)return RG_CAUTION;
  return RG_CLEAR;
}
void storeScan(){
  float cm=readUsMedian();uint8_t rs=classify(cm);uint32_t now=millis();
  if(scanPos==POS_LEFT){distL=cm;rangeL=rs;distLms=now;}
  else if(scanPos==POS_RIGHT){distR=cm;rangeR=rs;distRms=now;}
  else{distC=cm;rangeC=rs;distCms=now;}
  String s="SCAN,";s+=scanName(scanPos);s+=",";
  if(isnan(cm))s+="INVALID,UNKNOWN";
  else{s+=String(cm,1);s+=",CM,";s+=rangeName(rs);}
  if(scanLogOn)sendLine(s);
}
void serviceSweep(){
  if(!sweepOn)return;
  if(!servoWaiting){servoAngle(scanAngle(scanPos));return;}
  if(millis()-servoMoveMs<SERVO_SETTLE_MS)return;
  servoWaiting=false;storeScan();nextScan();
}

// ---------------- Freshness / fusion ----------------
bool fresh(uint32_t t,uint32_t maxAge){return t&&millis()-t<=maxAge;}
bool cameraFresh(){return fresh(cameraMs,CAMERA_STALE_MS);}
bool centerFresh(){return fresh(distCms,CENTER_STALE_MS);}
bool leftFresh(){return fresh(distLms,SIDE_STALE_MS);}
bool rightFresh(){return fresh(distRms,SIDE_STALE_MS);}

bool cameraGate(){
  if(mode==US_ONLY)return true;
  return cameraFresh()&&camEdge==CE_SAFE;
}

int chooseTurn(){
  bool lOK=leftFresh()&&rangeL==RG_CLEAR;
  bool rOK=rightFresh()&&rangeR==RG_CLEAR;
  if(!lOK&&!rOK)return 0;
  if(lOK&&!rOK)return -1;
  if(!lOK&&rOK)return 1;

  float ls=isnan(distL)?0:distL;
  float rs=isnan(distR)?0:distR;

  // Camera is a secondary hint; US-100 remains the physical veto.
  if(mode==FUSION&&cameraFresh()){
    if(camL==CS_BLOCKED)ls-=20.0f; else if(camL==CS_FREE)ls+=5.0f;
    if(camR==CS_BLOCKED)rs-=20.0f; else if(camR==CS_FREE)rs+=5.0f;
  }

  float diff=ls-rs;
  if(diff>=5.0f)return -1;
  if(diff<=-5.0f)return 1;
  if(previousTurn)return previousTurn;
  return -1;
}

// ---------------- Auto navigation ----------------
void serviceTurn(){
  if(!turnUntilMs)return;
  if((int32_t)(millis()-turnUntilMs)>=0){
    stopRobot(nullptr);
    invalidateRangesAfterTurn();
    scanPos=POS_CENTER_A;
    servoWaiting=false;
  }
}

void serviceAuto(){
  if(!armed||!autoOn){
    if(recoveryState!=REC_NONE){
      stopRobot(nullptr);
      clearRecovery();
    }
    return;
  }

  if(turnUntilMs)return;

  // If Atlas is already recovering, recovery owns the motors until it finishes.
  if(serviceRecovery())return;

  // Explicit EDGE is a recoverable front cliff hazard:
  // STOP -> short BACKOFF -> wait for SAFE -> side scan -> TURN.
  // UNKNOWN/stale camera remains fail-safe STOP only.
  if(mode==FUSION && cameraFresh() && camEdge==CE_EDGE){
    startRecovery(REC_CAUSE_EDGE,"CAMERA_EDGE","EDGE");
    return;
  }

  if(!cameraGate()){
    if(motion!=STOPPED)stopRobot("CAMERA_GATE");
    return;
  }

  if(!centerFresh()||rangeC==RG_UNKNOWN){
    if(motion!=STOPPED)stopRobot("CENTER_UNKNOWN_OR_STALE");
    return;
  }

  // A nearby wall/obstacle gets one short reverse to create turning space.
  // CAUTION and BLOCKED both use recovery, so Atlas actively backs away
  // instead of stopping in a cramped position.
  if(rangeC==RG_BLOCKED || rangeC==RG_CAUTION){
    if(rangeC==RG_BLOCKED)startRecovery(REC_CAUSE_WALL,"CENTER_BLOCKED","WALL");
    else startRecovery(REC_CAUSE_WALL,"CENTER_CAUTION","WALL");
    return;
  }

  if(rangeC==RG_CLEAR){
    if(motion!=FORWARD){
      if(motion==STOPPED)driveWithStartupBoost(drivePwm,drivePwm);
      else drive(drivePwm,drivePwm);
      motion=FORWARD;
      sendLine("AUTO,ACTION,FORWARD");
    }
    return;
  }

  // Defensive fallback: normally unreachable because every valid range
  // is CLEAR, CAUTION or BLOCKED.
  if(motion!=STOPPED)stopRobot("AUTO_FALLBACK");
}

// ---------------- Status ----------------
void status(){
  long l,r;noInterrupts();l=encL;r=encR;interrupts();
  String s="STATUS,";s+=armed?"ARMED":"DISARMED";
  s+=",AUTO,";s+=autoOn?"ON":"OFF";
  s+=",MODE,";s+=modeName();
  s+=",MOTION,";s+=motionName(motion);
  s+=",RECOVERY,";s+=recoveryName();
  s+=",L,";s+=isnan(distL)?"NA":String(distL,1);s+=",";s+=rangeName(rangeL);
  s+=",C,";s+=isnan(distC)?"NA":String(distC,1);s+=",";s+=rangeName(rangeC);
  s+=",R,";s+=isnan(distR)?"NA":String(distR,1);s+=",";s+=rangeName(rangeR);
  s+=",ENC_L,";s+=String(l);s+=",ENC_R,";s+=String(r);
  s+=",CAM_EDGE,";s+=camEdgeName();s+=",CAM_L,";s+=camSideName(camL);s+=",CAM_R,";s+=camSideName(camR);
  sendLine(s);
}

void help(){
  sendLine("HELP,PING|STATUS|ARM|DISARM|STOP|HB|HEARTBEAT");
  sendLine("HELP,AUTO,ON|AUTO,OFF");
  sendLine("HELP,MODE,US_ONLY|MODE,FUSION");
  sendLine("HELP,SWEEP,ON|SWEEP,OFF|SCANLOG,ON|SCANLOG,OFF");
  sendLine("HELP,PWM,<0-255>|FWD|BACK|LEFT|RIGHT");
  sendLine("HELP,CAM,EDGE,SAFE|EDGE|UNKNOWN");
  sendLine("HELP,CAM,LEFT,FREE|BLOCKED|UNKNOWN");
  sendLine("HELP,CAM,RIGHT,FREE|BLOCKED|UNKNOWN");
}

// ---------------- Camera command ----------------
void cameraCmd(const String& u){
  if(u=="CAM,EDGE,SAFE")camEdge=CE_SAFE;
  else if(u=="CAM,EDGE,EDGE")camEdge=CE_EDGE;
  else if(u=="CAM,EDGE,UNKNOWN")camEdge=CE_UNKNOWN;
  else if(u=="CAM,LEFT,FREE")camL=CS_FREE;
  else if(u=="CAM,LEFT,BLOCKED")camL=CS_BLOCKED;
  else if(u=="CAM,LEFT,UNKNOWN")camL=CS_UNKNOWN;
  else if(u=="CAM,RIGHT,FREE")camR=CS_FREE;
  else if(u=="CAM,RIGHT,BLOCKED")camR=CS_BLOCKED;
  else if(u=="CAM,RIGHT,UNKNOWN")camR=CS_UNKNOWN;
  else{sendLine("ERROR,BAD_CAMERA_COMMAND");return;}
  cameraMs=millis();sendLine("ACK,CAMERA");
}

// ---------------- Command parser ----------------
void command(String cmd,bool fromNet){
  cmd.trim();if(!cmd.length())return;
  String u=cmd;u.toUpperCase();
  if(u.startsWith("CMD,"))u=u.substring(4); // Stage 10 compatibility
  if(fromNet){networkControl=true;lastNetMs=millis();}

  if(u=="HELP"||u=="H"){help();return;}
  if(u=="PING"){sendLine("PONG");return;}
  if(u=="STATUS"){status();return;}
  if(u=="HB"||u=="HEARTBEAT"){sendLine("ACK,HEARTBEAT");return;}

  if(u=="ARM"){armed=true;stopRobot(nullptr);sendLine("ACK,ARM");return;}
  if(u=="DISARM"){autoOn=false;armed=false;stopRobot("DISARM");clearRecovery();sendLine("ACK,DISARM");return;}
  if(u=="STOP"){autoOn=false;stopRobot("USER_STOP");clearRecovery();sendLine("ACK,STOP");return;}

  if(u=="AUTO,ON"){
    if(!armed){sendLine("ERROR,NOT_ARMED");return;}
    autoOn=true;sendLine("ACK,AUTO,ON");return;
  }
  if(u=="AUTO,OFF"){autoOn=false;stopRobot("AUTO_OFF");clearRecovery();sendLine("ACK,AUTO,OFF");return;}

  if(u=="MODE,US_ONLY"){mode=US_ONLY;sendLine("ACK,MODE,US_ONLY");return;}
  if(u=="MODE,FUSION"){mode=FUSION;sendLine("ACK,MODE,FUSION");return;}

  if(u=="SWEEP,ON"){sweepOn=true;servoWaiting=false;sendLine("ACK,SWEEP,ON");return;}
  if(u=="SWEEP,OFF"){sweepOn=false;servoAngle(ANG_CENTER);sendLine("ACK,SWEEP,OFF");return;}

  if(u=="SCANLOG,ON"){scanLogOn=true;sendLine("ACK,SCANLOG,ON");return;}
  if(u=="SCANLOG,OFF"){scanLogOn=false;sendLine("ACK,SCANLOG,OFF");return;}

  if(u.startsWith("PWM,")){
    drivePwm=constrain(u.substring(u.indexOf(',')+1).toInt(),0,255);
    sendLine("ACK,PWM,"+String(drivePwm));return;
  }

  if(u=="FWD"){
    autoOn=false;if(!armed){sendLine("ERROR,NOT_ARMED");return;}
    if(motion==STOPPED)driveWithStartupBoost(drivePwm,drivePwm);else drive(drivePwm,drivePwm);
    motion=FORWARD;sendLine("ACK,FWD");return;
  }
  if(u=="BACK"){
    autoOn=false;if(!armed){sendLine("ERROR,NOT_ARMED");return;}
    if(motion==STOPPED)driveWithStartupBoost(-drivePwm,-drivePwm);else drive(-drivePwm,-drivePwm);
    motion=BACKWARD;sendLine("ACK,BACK");return;
  }
  if(u=="LEFT"){autoOn=false;if(!armed){sendLine("ERROR,NOT_ARMED");return;}startLeftTurn();return;}
  if(u=="RIGHT"){autoOn=false;if(!armed){sendLine("ERROR,NOT_ARMED");return;}startRightTurn();return;}

  if(u.startsWith("CAM,")){cameraCmd(u);return;}
  sendLine("ERROR,UNKNOWN_COMMAND,"+u);
}

// ---------------- Serial/TCP input ----------------
void serviceSerial(){
  while(Serial.available()){
    char c=(char)Serial.read();serialLastByteMs=millis();
    if(c=='\r'||c=='\n'){
      if(serialBuf.length()){command(serialBuf,false);serialBuf="";}
    }else if(serialBuf.length()<160)serialBuf+=c;
  }
  // Also works if Serial Monitor is set to "No line ending".
  if(serialBuf.length()&&millis()-serialLastByteMs>=COMMAND_IDLE_FLUSH_MS){command(serialBuf,false);serialBuf="";}
}

void acceptClient(){
  if(client&&client.connected())return;
  WiFiClient c=server.available();
  if(c){client=c;netBuf="";hadClient=true;networkControl=false;lastNetMs=millis();sendLine("WIFI,CLIENT,CONNECTED");}
}

void serviceNet(){
  if(!(client&&client.connected()))return;
  while(client.available()){
    char c=(char)client.read();netLastByteMs=millis();
    if(c=='\r'||c=='\n'){
      if(netBuf.length()){command(netBuf,true);netBuf="";}
    }else if(netBuf.length()<160)netBuf+=c;
  }
  if(netBuf.length()&&millis()-netLastByteMs>=COMMAND_IDLE_FLUSH_MS){command(netBuf,true);netBuf="";}
}

void networkSafety(){
  if(client&&client.connected()){
    hadClient=true;
    if(networkControl&&millis()-lastNetMs>HB_TIMEOUT_MS){
      autoOn=false;armed=false;networkControl=false;stopRobot("HEARTBEAT_TIMEOUT");sendLine("ERROR,HEARTBEAT_TIMEOUT,DISARMED");
    }
    return;
  }
  if(hadClient&&networkControl&&(autoOn||motion!=STOPPED)){
    autoOn=false;armed=false;networkControl=false;stopRobot("NETWORK_DISCONNECT");Serial.println("ERROR,NETWORK_DISCONNECT,DISARMED");
  }
  hadClient=false;
}

// ---------------- Setup / loop ----------------
uint32_t lastStatusMs=0;

void setup(){
  Serial.begin(115200);delay(600);

  pinMode(L_IN1,OUTPUT);pinMode(L_IN2,OUTPUT);
  pinMode(R_IN1,OUTPUT);pinMode(R_IN2,OUTPUT);

  bool okL=pwmAttachCompat(L_EN,CH_L,MOTOR_FREQ,MOTOR_BITS);
  bool okR=pwmAttachCompat(R_EN,CH_R,MOTOR_FREQ,MOTOR_BITS);
  bool okS=pwmAttachCompat(SERVO_PIN,CH_SERVO,SERVO_FREQ,SERVO_BITS);
  if(!okL||!okR||!okS){Serial.println("FATAL,PWM_ATTACH_FAILED");while(true)delay(1000);}

  stopRobot(nullptr);

  pinMode(ENC_L_A,INPUT_PULLUP);pinMode(ENC_L_B,INPUT_PULLUP);
  pinMode(ENC_R_A,INPUT_PULLUP);pinMode(ENC_R_B,INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_L_A),isrL,CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_R_A),isrR,CHANGE);

  pinMode(US_TRIG,OUTPUT);pinMode(US_ECHO,INPUT);digitalWrite(US_TRIG,LOW);

  scanPos=POS_CENTER_A;servoAngle(ANG_CENTER);

  WiFi.mode(WIFI_AP);
  bool apOK=WiFi.softAP(AP_SSID,AP_PASS);
  if(apOK)server.begin();else Serial.println("ERROR,WIFI_AP_FAILED");

  Serial.println();
  Serial.println("================================================");
  Serial.println("ATLAS 6.0 INTEGRATED RELEASE CANDIDATE V3.4 AUTO RECOVERY");
  Serial.println("================================================");
  Serial.print("ARDUINO_ESP32_MAJOR,");Serial.println(ESP_ARDUINO_VERSION_MAJOR);
  Serial.print("WIFI,SSID,");Serial.println(AP_SSID);
  Serial.print("WIFI,IP,");Serial.println(WiFi.softAPIP());
  Serial.print("WIFI,TCP_PORT,");Serial.println(TCP_PORT);
  Serial.println("DISTANCE,BLOCKED,<10CM");
  Serial.println("DISTANCE,CAUTION,10_TO_<15CM");
  Serial.println("DISTANCE,CLEAR,>=15CM");
  Serial.println("SERVO,SCAN,5-90-175-90,CONTINUOUS");
  Serial.print("MOTOR,CRUISE_PWM,");Serial.println(DEFAULT_DRIVE_PWM);
  Serial.print("MOTOR,STARTUP_BOOST_PWM,");Serial.println(STARTUP_BOOST_PWM);
  Serial.print("MOTOR,STARTUP_BOOST_MS,");Serial.println(STARTUP_BOOST_MS);
  Serial.println("MOTOR,DIRECTION_MAP,V3.3_FIXED");
  Serial.print("RECOVERY,BACKOFF_PWM,");Serial.println(BACKOFF_CRUISE_PWM);
  Serial.print("RECOVERY,BACKOFF_AFTER_BOOST_MS,");Serial.println(BACKOFF_AFTER_BOOST_MS);
  Serial.println("RECOVERY,EDGE,STOP_BACKOFF_WAIT_SAFE_SCAN_TURN");
  Serial.println("RECOVERY,WALL_CAUTION_OR_BLOCKED,STOP_BACKOFF_SCAN_TURN");
  Serial.println("SCANLOG,OFF,BY_DEFAULT");
  Serial.print("ENCODER,LEFT_PPR,");Serial.println(LEFT_PPR,2);
  Serial.print("ENCODER,RIGHT_PPR,");Serial.println(RIGHT_PPR,2);
  Serial.print("WHEEL_CIRCUMFERENCE_CM,");Serial.println(WHEEL_CIRC_CM,2);
  Serial.println("BOOT,DISARMED,AUTO_OFF,MODE_US_ONLY,SWEEP_ON,SCANLOG_OFF");
  help();
}

void loop(){
  acceptClient();
  serviceSerial();serviceNet();
  serviceSweep();
  serviceTurn();serviceAuto();
  networkSafety();

  if(millis()-lastStatusMs>=1000){lastStatusMs=millis();status();}
  delay(2);
}
