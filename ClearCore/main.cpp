#include "ClearCore.h"
#include "cmath"

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

//For clearcore 2000 pulses per sec is equal to 1rpm output with 100:1 gearbox attached.
// Define the velocity and acceleration limits to be used for each move
int32_t velocityLimit = 2500; // pulses per sec
int32_t accelerationLimit = 100000; // pulses per sec^2

int32_t MotorZvelocityLimit = 200; // pulses per sec
int32_t MotorZaccelerationLimit = 100000; // pulses per sec^2

void MoveDistance(int32_t distance);
void RunTest();
void ReadVoltage(int count);
void MoveXaxis(int32_t distance);
void MoveYaxis(int32_t distance);
void MoveZaxis(int32_t distance);
void MoveA(int32_t distance);
void MoveB(int32_t distance);
void RunXTest();
void RunYTest();
void RunZTest();
float ReadXVoltage();
float ReadYVoltage();
float ReadZVoltage();

int main() {
    // Sets the input clocking rate.
    MotorMgr.MotorInputClocking(MotorManager::CLOCK_RATE_LOW);

    // Sets all motor connectors into step and direction mode.
    MotorMgr.MotorModeSet(MotorManager::MOTOR_ALL,
                          Connector::CPM_MODE_STEP_AND_DIR);

    // These lines may be uncommented to invert the output signals of the
    // Enable, Direction, and HLFB lines. Some motors may have input polarities
    // that are inverted from the ClearCore's polarity.
    motorA.PolarityInvertSDEnable(true);
    motorB.PolarityInvertSDEnable(true);
	motorZ1.PolarityInvertSDEnable(true);
	motorZ2.PolarityInvertSDEnable(true);
    //motor.PolarityInvertSDDirection(true);
    //motor.PolarityInvertSDHlfb(true);

    // Sets the maximum velocity for each move
    motorA.VelMax(velocityLimit);
	motorB.VelMax(velocityLimit);
	motorZ1.VelMax(MotorZvelocityLimit);
	motorZ2.VelMax(MotorZvelocityLimit);

    // Set the maximum acceleration for each move
    motorA.AccelMax(accelerationLimit);
	motorB.AccelMax(accelerationLimit);
	motorZ1.AccelMax(MotorZaccelerationLimit);
	motorZ2.AccelMax(MotorZaccelerationLimit);

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
		if((char)input=='1'){
			//Starts tests that moves motors
			RunTest();
			//Test finishes
			SerialPort.SendLine("0");
			input = 0;
		}
		
		if((char)input=='x'){
		
			//RunXTest();
			MoveXaxis(-4000);
			SerialPort.SendLine("0");
			input = 0;	
		}
		
		if((char)input=='y'){
			//RunYTest();
			MoveYaxis(-4000);
			SerialPort.SendLine("0");
			input = 0;
		}
		
		if((char)input=='z'){
			
			for(int i=0;i<10;i++){
				ReadVoltage(0);
				
				Delay_ms(1000);
				MoveZaxis(-50);
				Delay_ms(1000);
				
				ReadVoltage(1);
				
				Delay_ms(1000);
				MoveZaxis(50);
				Delay_ms(1000);
				
				ReadVoltage(2);
				SerialPort.SendLine("  ");
			}
			SerialPort.SendLine("0");
			input = 0;
		}
		//Moves right on x axis
		if((char)input=='a'){
			MoveA(6000);
			SerialPort.SendLine("0");
			input = 0;
		}
		//Moves left on x axis
		if((char)input=='s'){
			MoveA(-6000);
			SerialPort.SendLine("0");
			input = 0;
		}
		//Moves right on x axis
		//Moves down on y axis
		if((char)input=='b'){
			//MoveB(6000);
			
			float mo=0,yvol,xvol,step;
			step=100;
			yvol = ReadYVoltage();
			xvol = ReadXVoltage();
			ReadVoltage(0);
			
			while(mo!=1){
				Delay_ms(500);
				yvol = ReadYVoltage();
				ReadVoltage(1);
				if(yvol==150){
					mo=1;
				}
				else if(yvol >= 149){
					MoveB(step);
				}
				else if(yvol <= 151 ){
					MoveB(-step);
				}
				

			}
			mo=0;
			
			while(mo!=1){
				Delay_ms(500);
				yvol = ReadYVoltage();
				ReadVoltage(2);
				
				if(yvol==135){
					mo=1;
				}
				
				else if(yvol >= 134){
					MoveB(step);
				}
				else if(yvol <= 136){
					MoveB(-step);
				}

				
			}
			mo=0;
			ReadVoltage(3);
			while(mo!=1){
				Delay_ms(500);
				yvol = ReadYVoltage();
				ReadVoltage(4);
				
				if(yvol==150){
					mo=1;
				}
				
				else if(yvol >= 149){
					MoveB(step);
				}
				else if(yvol <= 151){
					MoveB(-step);
				}


			}
			ReadVoltage(5);
			
			
			mo=0;
			while(mo!=1){
				
				Delay_ms(500);
				xvol = ReadXVoltage();
				ReadVoltage(6);
				
				if(xvol==150){
					mo=1;
				}
				else if(xvol >= 149){
					MoveA(step);
				}
				else if(xvol <= 151 ){
					MoveA(-step);
				}


			}
			

			mo=0;
			while(mo!=1){
				
				Delay_ms(500);
				xvol = ReadXVoltage();
				ReadVoltage(7);
				if(xvol==135){
					mo=1;
				}
				else if(xvol >= 134){
					MoveA(step);
				}
				else if(xvol <= 136 ){
					MoveA(-step);
				}


				
			}
			
			mo=0;
			while(mo!=1){
				
				Delay_ms(500);
				xvol = ReadXVoltage();
				ReadVoltage(8);
				
				if(xvol==150){
					mo=1;
				}
				else if(xvol >= 149){
					MoveA(step);
				}
				else if(xvol <= 151 ){
					MoveA(-step);
				}


			}
			
			//4400
			/*
			for(int i=0;i<5;i++){
			ReadVoltage(1);
			Delay_ms(1000);
			MoveB(15000);
			Delay_ms(1000);
			ReadVoltage(1);
			Delay_ms(1000);
			MoveB(-15000);
			Delay_ms(1000);
			ReadVoltage(1);
			SerialPort.SendLine("  ");
			}
			*/
			SerialPort.SendLine("0");
			input = 0;
		}
		//Moves left on x axis
		if((char)input=='n'){
			MoveB(-6000);
			SerialPort.SendLine("0");
			input = 0;
		}
    }
}

void MoveA(int32_t distance){
	
	motorA.Move(distance);
	while (!motorA.StepsComplete()) {
		continue;
	}
}
void MoveB(int32_t distance){
	

	motorB.Move(distance);
	while (!motorB.StepsComplete()) {
		continue;
	}
}

//Negative X moves carriage left

void RunXTest(){
	//2546
	//160,000 is 1 rotation
	//for(int i=0;i<20;i++)
	//{
			//MoveXaxis(-14000);
			//ReadVoltage(1);
			//MoveXaxis(14000);
			
	//}
	ReadVoltage(1);
	Delay_ms(200);
	MoveXaxis(-1000);
	Delay_ms(200);
	ReadVoltage(1);
	Delay_ms(200);
	MoveXaxis(1000);
	Delay_ms(200);
	ReadVoltage(1);
}
//Positive value moves y-axis up
void RunYTest(){
	/*for(int i=0;i<20;i++){
	MoveYaxis(-20000);
	MoveYaxis(20000);
	}*/
	MoveYaxis(-5000);
}

void RunZTest(){
	
	
	MoveZaxis(-10);
	//MoveZaxis(100);
}


void TestSensor(){
		float xD,yD,zD;
		xD = ReadXVoltage();
		yD = ReadYVoltage();
		zD = ReadZVoltage();
			
		while(xD!=2.15 && yD!=2.00){
				
			if(yD < 2.00){
				MoveYaxis(1);
			}
			else if(yD > 2.00){
				MoveYaxis(-1);
			}
				
			if(xD < 2.15){
				MoveXaxis(1);
			}
			else if(xD > 2.15){
				MoveXaxis(-1);
			}
			
			xD = ReadXVoltage();
			yD = ReadYVoltage();			
				
		}
		
		ReadVoltage(1);
		while(xD!=1.85 && yD!=2.00){
				
			if(yD < 2.00){
				MoveYaxis(1);
			}
			else if(yD > 2.00){
				MoveYaxis(-1);
			}
				
			if(xD < 1.85){
				MoveXaxis(1);
			}
			else if(xD > 1.85){
				MoveXaxis(-1);
			}
			
			xD = ReadXVoltage();
			yD = ReadYVoltage();
		}
			
		ReadVoltage(2);
		while(xD!=2.00 && yD!=2.15){

			if(xD < 2.00){
				MoveXaxis(1);
			}
			else if(xD > 2.00){
				MoveXaxis(-1);
			}
			if(yD < 2.15){
				MoveYaxis(1);
			}
			else if(yD > 2.15){
				MoveYaxis(-1);
			}
			
			xD = ReadXVoltage();
			yD = ReadYVoltage();
		}
			
		ReadVoltage(3);
			
		while(xD!=2.00 && yD!=1.85){

			if(xD < 2.00){
				MoveXaxis(1);
			}
			else if(xD > 2.00){
				MoveXaxis(-1);
			}
			if(yD < 1.85){
				MoveYaxis(1);
			}
			else if(yD > 1.85){
				MoveYaxis(-1);
			}
			xD = ReadXVoltage();
			yD = ReadYVoltage();
			
		}
			
		ReadVoltage(4);
		while(xD!=2.00 && yD!=1.85 && zD!=1.85){

			if(xD < 2.00){
				MoveXaxis(1);
			}
			else if(xD > 2.00){
				MoveXaxis(-1);
			}
			
			if(yD < 1.85){
				MoveYaxis(1);
			}
			else if(yD > 1.85){
				MoveYaxis(-1);
			}
			
			if(zD < 1.85){
				MoveZaxis(1);
			}
			else if(zD > 1.85){
				MoveZaxis(-1);
			}
			xD = ReadXVoltage();
			yD = ReadYVoltage();
			zD = ReadZVoltage();
		}
		
		ReadVoltage(5);
		while(xD!=2.00 && yD!=1.85 && zD!=2.15){

			if(xD < 2.00){
				MoveXaxis(1);
			}
			else if(xD > 2.00){
				MoveXaxis(-1);
			}
			
			if(yD < 1.85){
				MoveYaxis(1);
			}
			else if(yD > 1.85){
				MoveYaxis(-1);
			}
			
			if(zD < 2.15){
				MoveZaxis(1);
			}
			else if(zD > 2.15){
				MoveZaxis(-1);
			}
			xD = ReadXVoltage();
			yD = ReadYVoltage();
			zD = ReadZVoltage();
		}
		ReadVoltage(6);
		
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
	MoveYaxis(100);

	//Reads voltage of sensor
	Delay_ms(1000);
	ReadVoltage(3);
	Delay_ms(1000);
			
	//Y-axis moves to other extreme
	MoveYaxis(-200);

	//Reads voltage of sensor
	Delay_ms(1000);
	ReadVoltage(4);
	Delay_ms(1000);
			
	//Centers y-axis
	MoveYaxis(100);
			
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

float ReadXVoltage(){
		int16_t xResult;
		xResult = ConnectorA12.State();
		
		// Convert the reading to a voltage.
		double xVoltage;
		xVoltage = 10.0 * xResult / ((1 << adcResolution) - 1);
		
		double Xmm;
		int X;
		Xmm = xVoltage * 0.35;
		X=round(Xmm*100);
		
		return X;
}

float ReadYVoltage(){
		int16_t yResult;
		yResult = ConnectorA11.State();
		
		// Convert the reading to a voltage.
		double yVoltage;
		yVoltage = 10.0 * yResult / ((1 << adcResolution) - 1);

		double Ymm;
		int Y;
		Ymm = yVoltage * 0.35;
		Y = round(Ymm*100);
		//SerialPort.SendLine(Y);
		
		
		return Y;

}

float ReadZVoltage(){
		int16_t zResult;
		zResult = ConnectorA10.State();
		
		// Convert the reading to a voltage.
		double zVoltage;
		zVoltage = 10.0 * zResult / ((1 << adcResolution) - 1);
		
		double Zmm;
		Zmm = zVoltage * 0.35;
		
		return Zmm;
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
}

//Moves sensor ring up on Y-axis
void MoveYaxis(int32_t distance){
	
	motorA.Move(distance);
	motorB.Move(-distance);
	while (!motorA.StepsComplete() && !motorB.StepsComplete()) {
		continue;
	}
}


//Moves shaft up or down(use negative value to change direction)
void MoveZaxis(int32_t distance){
	
	motorZ1.Move(distance);
	motorZ2.Move(distance);
	while (!motorZ1.StepsComplete() && !motorZ2.StepsComplete()) {
		continue;
	}
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
