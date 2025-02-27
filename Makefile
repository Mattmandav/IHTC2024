# the compiler to use
CC = clang++

# compiler flags:
#  -g    adds debugging information to the executable file
#  -Wall turns on most, but not all, compiler warnings
CFLAGS  = -g -Wall

  
# the name to use for both the target source file, and the output file:
TARGET = .IHTP_Validator
  
all: $(TARGET)
  
$(TARGET): $(TARGET).cc
	$(CC) $(CFLAGS) -o $(TARGET) $(TARGET).cc $(LFLAGS)
