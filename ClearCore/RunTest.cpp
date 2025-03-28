#include "ClearCore.h"

// Specifies which motor to move.
// Options are: ConnectorM0, ConnectorM1, ConnectorM2, or ConnectorM3.
//Defines motors to their connectors
#define motorA ConnectorM0
#define motorB ConnectorM1
#define motorZ1 ConnectorM2
#define motorZ2	ConnectorM3

// Select the baud rate to match the target serial device
#define baudRate 9600
#define adcResolution 12

// Specify which serial to use: ConnectorUsb, ConnectorCOM0, or ConnectorCOM1.
#define SerialPort ConnectorUsb
#define InputPort ConnectorUsb

// Define the velocity and acceleration limits to be used for each move
int32_t velocityLimit = 1000; // pulses per sec
int32_t accelerationLimit = 10000; // pulses per sec^2

// Declares our user-defined helper function, which is used to command moves to
// the motor. The definition/implementation of this function is at the  bottom
// of the example.
void MoveDistance(int32_t distance);
void RunTest();
void ReadVoltage(int count);
void MoveXaxis(int32_t distance);
void MoveUpYaxis(int32_t distance);
void MoveDownYaxis(int32_t distance);
void MoveZaxis(int32_t distance);

int main() {
    // Sets the input clocking rate.
    MotorMgr.MotorInputClocking(MotorManager::CLOCK_RATE_NORMAL);

    // Sets all motor connectors into step and direction mode.
    MotorMgr.MotorModeSet(MotorManager::MOTOR_ALL,
                          Connector::CPM_MODE_STEP_AND_DIR);

    // These lines may be uncommented to invert the output signals of the
    // Enable, Direction, and HLFB lines. Some motors may have input polarities
    // that are inverted from the ClearCore's polarity.
    motorA.PolarityInvertSDEnable(true);
    motorB.PolarityInvertSDEnable(true);
    //motor.PolarityInvertSDDirection(true);
    //motor.PolarityInvertSDHlfb(true);

    // Sets the maximum velocity for each move
    motorA.VelMax(velocityLimit);
	  motorB.VelMax(velocityLimit);
	  motorZ1.VelMax(velocityLimit);
	  motorZ2.VelMax(velocityLimit);

    // Set the maximum acceleration for each move
    motorA.AccelMax(accelerationLimit);
	  motorB.AccelMax(accelerationLimit);
	  motorZ1.AccelMax(accelerationLimit);
	  motorZ2.AccelMax(accelerationLimit);

    // Sets up serial communication and waits up to 5 seconds for a port to open.
    // Serial communication is not required for this example to run.
    SerialPort.Mode(Connector::USB_CDC);
    SerialPort.Speed(baudRate);
    uint32_t timeout = 5000;
    uint32_t startTime = Milliseconds();
    SerialPort.PortOpen();
    while(!SerialPort && Milliseconds() - startTime < timeout) {
        continue;
    }

	  InputPort.Mode(Connector::USB_CDC);
	  InputPort.Speed(baudRate);
    AdcMgr.AdcResolution(adcResolution);

    // Enables the motor.
    motorA.EnableRequest(true);
	  motorB.EnableRequest(true);
	  motorZ1.EnableRequest(true);
	  motorZ2.EnableRequest(true);

    // Waits for HLFB to assert. Uncomment these lines if your motor has a
    // "servo on" feature and it is wired to the HLFB line on the connector.
    //SerialPort.SendLine("Waiting for HLFB...");
    //while (motor.HlfbState() != MotorDriver::HLFB_ASSERTED) {
    //    continue;
    //}
	  int16_t input=0;
	  while(true){
			
		  input = InputPort.CharGet();
		  while((char)input=='1'){
			//Starts tests that moves motors
			RunTest();
			
			//Test finishes
			SerialPort.SendLine("0");
			input = 0;
		}
    }
}

void RunTest(){
	//Read voltage while centered
	ReadVoltage(0);
			
	//X-axis moves to one extreme
	MoveXaxis(18000);

	//Reads voltage of sensor
	Delay_ms(1000);
	ReadVoltage(1);
	Delay_ms(1000);
			
	//X-axis moves to other extreme
	MoveXaxis(-2000);

	//Reads voltage of sensor
	Delay_ms(1000);
	ReadVoltage(2);
	Delay_ms(1000);
			
	//Centers x-axis
	MoveXaxis(100);
			
	//Y-axis moves to one extreme
	MoveUpYaxis(10000);

	//Reads voltage of sensor
	Delay_ms(1000);
	ReadVoltage(3);
	Delay_ms(1000);
			
	//Y-axis moves to other extreme
	MoveDownYaxis(200);

	//Reads voltage of sensor
	Delay_ms(1000);
	ReadVoltage(4);
	Delay_ms(1000);
			
	//Centers y-axis
	MoveUpYaxis(100);
			
	//Z-axis moves to one extreme
	MoveZaxis(150);

	//Reads voltage of sensor
	Delay_ms(1000);
	ReadVoltage(5);
	Delay_ms(1000);
			
	//Z-axis moves to other extreme
	MoveZaxis(-300);

	//Reads voltage of sensor
	Delay_ms(1000);
	ReadVoltage(6);
	Delay_ms(1000);
			
	//Centers z-axis
	MoveZaxis(150);	
}

void ReadVoltage(int count){
	int16_t xResult,yResult,zResult;
	xResult = ConnectorA12.State();
	yResult = ConnectorA11.State();
	zResult = ConnectorA10.State();
				
	// Convert the reading to a voltage.
	double xVoltage,yVoltage,zVoltage;
	xVoltage = 10.0 * xResult / ((1 << adcResolution) - 1);
	yVoltage = 10.0 * yResult / ((1 << adcResolution) - 1);
	zVoltage = 10.0 * zResult / ((1 << adcResolution) - 1);
				
	double Xmm,Ymm,Zmm;
	Xmm = xVoltage * 0.35;
	Ymm = yVoltage * 0.35;
	Zmm = zVoltage * 0.35;
				
	// Display the voltage reading to the serial port.
	SerialPort.Send(count);
	SerialPort.Send(",");
	SerialPort.Send(Xmm);
	SerialPort.Send(",");
	SerialPort.Send(Ymm);
	SerialPort.Send(",");
	SerialPort.SendLine(Zmm);

}

//Moves sensor ring on X-axis(positive distance moves left, negative distance moves right)
void MoveXaxis(int32_t distance){
	
	motorA.Move(distance);
	motorB.Move(distance);
	while (!motorA.StepsComplete() && !motorB.StepsComplete()) {
		continue;
	}
	
	Delay_ms(200);
}

//Moves sensor ring up on Y-axis
void MoveUpYaxis(int32_t distance){
	
	motorA.Move(-distance);
	motorB.Move(distance);
	while (!motorA.StepsComplete() && !motorB.StepsComplete()) {
		continue;
	}
	Delay_ms(200);
}

//Moves sensor ring down on Y-axis
void MoveDownYaxis(int32_t distance){

	motorA.Move(distance);
	motorB.Move(-distance);
	while (!motorA.StepsComplete() && !motorB.StepsComplete()) {
		continue;
	}
	Delay_ms(200);
}

//Moves shaft up or down(use negative value to change direction)
void MoveZaxis(int32_t distance){
	
	motorZ1.Move(distance);
	motorZ2.Move(distance);
	while (!motorZ1.StepsComplete() && !motorZ2.StepsComplete()) {
		continue;
	}
	Delay_ms(200);
}

/*------------------------------------------------------------------------------
 * MoveDistance
 *
 *    Command "distance" number of step pulses away from the current position
 *    Prints the move status to the USB serial port
 *    Returns when step pulses have completed
 *
 * Parameters:
 *    int distance  - The distance, in step pulses, to move
 *
 * Returns: None
 */
void MoveDistance(int32_t distance) {
    SerialPort.Send("Moving distance: ");
    SerialPort.SendLine(distance);

    // Command the move of incremental distance
    motorA.Move(distance);

    // Waits for all step pulses to output
    SerialPort.SendLine("Moving... Waiting for the step output to finish...");
    while (!motorA.StepsComplete()) {
        continue;
    }

    SerialPort.SendLine("Steps Complete");
}
//------------------------------------------------------------------------------
