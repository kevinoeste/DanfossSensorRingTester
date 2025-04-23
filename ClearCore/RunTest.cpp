#include "ClearCore.h"
#include "cmath"

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
		
			RunXTest();
			SerialPort.SendLine("0");
			input = 0;	
		}
		
		if((char)input=='y'){
			RunYTest();
			SerialPort.SendLine("0");
			input = 0;
		}
		
		if((char)input=='z'){
			RunZTest();
			SerialPort.SendLine("0");
			input = 0;
		}
    }
}



//Negative X moves carriage left

void RunXTest(){
	//2546
	//160,000 is 1 rotation
	float mo=0,xvol;
	int step;
	step=100;

	xvol = ReadXVoltage();

	ReadVoltage(0);
	//X-axis
	//Centers x-axis
	mo=0;
	while(mo!=1){
		
		Delay_ms(500);
		xvol = ReadXVoltage();
		if(xvol==150){
			Delay_ms(1000);
			ReadVoltage(1);
			Delay_ms(1000);
			mo=1;
		}
		else if(xvol >= 151){
			MoveA(step);
		}
		else if(xvol <= 149){
			MoveA(-step);
		}
	}
	
	for(int i=0;i<20;i++){
		ReadVoltage(1);
		MoveXaxis(-15000);
		ReadVoltage(1);
		MoveXaxis(15000);
		ReadVoltage(1);
	}

}
//Positive value moves y-axis up
void RunYTest(){
	float mo=0,yvol;
	int step;
	step=100;
	
	while(mo!=1){
		
		Delay_ms(500);
		yvol = ReadYVoltage();

		if(yvol==150){
			Delay_ms(1000);
			ReadVoltage(3);
			Delay_ms(1000);
			mo=1;
		}
		else if(yvol >= 151){
			MoveB(step);
		}
		else if(yvol <= 149 ){
			MoveB(-step);
		}
	}
	
	for(int i=0;i<20;i++){
		ReadVoltage(3);
		MoveYaxis(-15000);
		ReadVoltage(3);
		MoveYaxis(15000);
		ReadVoltage(3);
	}
}

void RunZTest(){
	float mo=0,zvol;
	int step;
	step=100;
	
	while(mo!=1){
				
		Delay_ms(500);
		zvol = ReadZVoltage();

		if(zvol==150){
			Delay_ms(1000);
			ReadVoltage(5);
			Delay_ms(1000);
			mo=1;
		}
		else if(zvol >= 151){
			MoveZaxis(step);
		}
		else if(zvol <= 149 ){
			MoveZaxis(-step);
		}
	}
	
	for(int i=0;i<20;i++){
		ReadVoltage(5);
		MoveZaxis(-40);
		ReadVoltage(5);
		MoveZaxis(40);
		ReadVoltage(5);
	}
}

void RunTest(){
			float mo=0,yvol,xvol,zvol;
			int step;
			step=100;
			yvol = ReadYVoltage();
			xvol = ReadXVoltage();
			zvol = ReadZVoltage();
			ReadVoltage(0);
//X-axis			
			//Centers x-axis	
			mo=0;
			while(mo!=1){
				
				Delay_ms(500);
				xvol = ReadXVoltage();
				if(xvol==150){
					Delay_ms(1000);
					ReadVoltage(1);
					Delay_ms(1000);
					mo=1;
				}
				else if(xvol >= 151){
					MoveA(step);
				}
				else if(xvol <= 149){
					MoveA(-step);
				}
			}

			//Moves x-axis 150micron
			mo=0;
			while(mo!=1){
				
				Delay_ms(500);
				xvol = ReadXVoltage();
				if(xvol==135){
					Delay_ms(1000);
					ReadVoltage(2);
					Delay_ms(1000);
					mo=1;
				}
				else if(xvol >= 136){
					MoveA(step);
				}
				else if(xvol <= 134){
					MoveA(-step);
				}
			}

			//Moves x-axis back to center
			mo=0;
			while(mo!=1){
				
				Delay_ms(500);
				xvol = ReadXVoltage();
				
				if(xvol==150){
					mo=1;
				}
				else if(xvol >= 151){
					MoveA(step);
				}
				else if(xvol <= 149 ){
					MoveA(-step);
				}
			}
//Y-axis
			while(mo!=1){
				
				Delay_ms(500);
				yvol = ReadYVoltage();

				if(yvol==150){
					Delay_ms(1000);
					ReadVoltage(3);
					Delay_ms(1000);
					mo=1;
				}
				else if(yvol >= 151){
					MoveB(step);
				}
				else if(yvol <= 149 ){
					MoveB(-step);
				}
			}
			

			mo=0;
			while(mo!=1){
				
				Delay_ms(500);
				yvol = ReadYVoltage();
				
				if(yvol==135){
					Delay_ms(1000);
					ReadVoltage(4);
					Delay_ms(1000);
					mo=1;
				}
				else if(yvol >= 136){
					MoveB(step);
				}
				else if(yvol <= 134){
					MoveB(-step);
				}
			}
			

			mo=0;
			while(mo!=1){
				
				Delay_ms(500);
				yvol = ReadYVoltage();
				
				if(yvol==150){
					mo=1;
				}
				else if(yvol >= 151){
					MoveB(step);
				}
				else if(yvol <= 149){
					MoveB(-step);
				}
			}
//Z-axis
			Delay_ms(1000);
			mo=0;
			while(mo!=1){
				
				Delay_ms(500);
				zvol = ReadZVoltage();

				if(zvol==150){
					Delay_ms(1000);
					ReadVoltage(5);
					Delay_ms(1000);
					mo=1;
				}
				else if(zvol >= 151){
					MoveZaxis(step);
				}
				else if(zvol <= 149 ){
					MoveZaxis(-step);
				}
			}
			
			mo=0;
			while(mo!=1){
				Delay_ms(500);
				zvol = ReadZVoltage();
				
				if(zvol==135){
					Delay_ms(1000);
					ReadVoltage(6);
					Delay_ms(1000);
					mo=1;
				}
				else if(zvol >= 136){
					MoveZaxis(step);
				}
				else if(zvol <= 134){
					MoveZaxis(-step);
				}
			}
			
			mo=0;
			while(mo!=1){
				
				Delay_ms(500);
				zvol = ReadZVoltage();
				if(zvol==150){
					mo=1;
				}
				else if(zvol >= 151){
					MoveZaxis(step);
				}
				else if(zvol <= 149){
					MoveZaxis(-step);
				}
			}
			SerialPort.SendLine("0");
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
		int Z;
		Z = round(Zmm*100);
		
		return Z;
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
