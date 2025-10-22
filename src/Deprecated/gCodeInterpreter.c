//ECE342 Project Vaughn O'Keeffe
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <dirent.h>
#include <unistd.h>

struct coordinate{
	float x;
	float y;

	//struct coordinate* next;
};

int filtercommands(char* currLine){
	int gcmd = 0;
	char* command = NULL;

	command = strstr(currLine, "G0");
	if(command != NULL){
		return gcmd;	
	}
	gcmd++;//1	
	command = strstr(currLine, "G1");
	if(command != NULL){
		return gcmd;	
	}
	gcmd++;//2	
	command = strstr(currLine, "G20");
	if(command != NULL){
		return gcmd;	
	}
	gcmd++;//3
	command = strstr(currLine, "G21");
	if(command != NULL){
		return gcmd;	
	}
	gcmd++;//4
	command = strstr(currLine, "G90");
	if(command != NULL){
		return gcmd;	
	}
	gcmd++;//5
	command = strstr(currLine, "G91");
	if(command != NULL){
		return gcmd;	
	}
	gcmd++;//6
	command = strstr(currLine, "M2");
	if(command != NULL){
		return gcmd;	
	}
	gcmd++;//7
	command = strstr(currLine, "M6");
	if(command != NULL){
		return gcmd;
	}
	gcmd++;//8
	command = strstr(currLine, "M72");
	if(command != NULL){
		return gcmd;	
	}
	gcmd++;//9
	//char* command = strstr(currLine, "M70");

	return gcmd;
}

void proccessmovements(char* currLine, int usemm, int useabsolute){
	//printf("Usemm: %d\n", usemm);
	char *saveptr;
	//tokenizes the title portion of a line from the movie file
	char *token = strtok_r(currLine, "X", &saveptr);
	token = strtok_r(NULL, " ", &saveptr);
	double xCoord = atof(token);
	if(usemm == 1){
		xCoord = xCoord / 25.4;
	}

	token = strtok_r(NULL, "Y", &saveptr);
	//token = strtok_r(NULL, " ", &saveptr);
	double yCoord = atof(token);
	if(usemm == 1){
		yCoord = yCoord / 25.4;
	}

	printf("(%f, %f)\n", xCoord, yCoord);

	return;
}

void processfile(char* filepath){
	//opens user specified file
	FILE* gcodefile = fopen(filepath, "r");
	//printf("here\n");
	//setup for getlines
	char* currLine = NULL;
	size_t length = 0;
	ssize_t nread;

	int usemm = -1;
	int useabsolute = -1;
	//reads each line from the file one by one and puts it into a Gcommand struct in the ll
	while ((nread = getline(&currLine, &length, gcodefile)) != -1){
		int commandnum = filtercommands(currLine);

		//printf("%d\n",commandnum);
		if(commandnum < 2){
			proccessmovements(currLine, usemm, useabsolute);
		}
		else if(commandnum == 2){
			usemm = 0;
			printf("Using Inches\n");
		}
		else if(commandnum == 3){
			usemm = 1;
			printf("Using Millimeters\n");
		}
		else if(commandnum == 4){
			useabsolute = 1;
			printf("Using Absolute Positioning Mode\n");
		}
		else if(commandnum == 5){
			useabsolute = 0;
			printf("Using Relative Positioning Mode\n");
		}
		else if(commandnum == 6){
			printf("End Program\n");
		}
		else if(commandnum == 7){
			printf("Tool Change\n");
		}
		else if(commandnum == 8){
			printf("Restore Modal State");
		}
	}
	//freeing the line from getline and closing the file
	free(currLine);
	fclose(gcodefile);
	
	//returning the head/start/first Gcommand of the ll
	return;
}

char* finduserfile(){
	printf("Enter the complete file name: ");
	//setup for getline
	char* lineEntered = NULL;
	size_t buffersize = 0;
	char* filename = NULL;
	int line = -1;
	//get user input
	line = getline(&lineEntered, &buffersize, stdin);
	//fixing the new line character from the getline command for future comparison
	lineEntered[strlen(lineEntered) - 1] = '\0';
	//setup for directory file searching
	char cwd[256];
	struct dirent* dirp;
	struct stat filestat;
	//open current directory
	DIR * currDir = opendir(getcwd(cwd, sizeof(cwd)));
	//iterate through the whole directory
	while((dirp = readdir(currDir)) != NULL){
		//pull and compare filenames with the potential new file name
		stat(dirp->d_name, &filestat);
		int result = strcmp(lineEntered, dirp->d_name);
		//if the file is found
		if(result == 0){
			//malloc prevented segfault
			filename = malloc((strlen(dirp->d_name)+1)*sizeof(char));
			strcpy(filename, dirp->d_name);
			//close directory
			closedir(currDir);
			return filename;
		}
	}
	printf("The file %s was not found. Try again\n", lineEntered);
	//close directory
	closedir(currDir);
	return NULL;
}

int main(){
	char* filename = finduserfile();
	if(filename == NULL){
		return 1;
	}
	processfile(filename);
	
	return 0;
}

  //G0 linear move
  //G1 linear move with speed
  //G90 set absolute movement
  //G91 set relative movement
  //G20 use inches
  //G21 use millimeters
  //M2 end program
  //M6 utensil change
  //M72 restor modal state
  //M70 save modal state