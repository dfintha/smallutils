BINARIES= \
	bin/bf \
	bin/pwgen \
	bin/bmi \
	bin/fire \
	bin/vigenere \
	bin/pdfcompress \
	bin/autoclick \
	bin/hexstrdump \
	bin/htmlm

.PHONY: all clean

all: $(BINARIES)
	@printf "Success!\n"

clean:
	@rm -rf bin
	@printf "Success!\n"

bin/bf: src/bf.c
	@printf "Compiling $@\n"
	@mkdir -p bin
	@gcc -Wall -Wextra -pedantic -std=c89 -O2 -s $< -o $@

bin/pwgen: src/pwgen.c
	@printf "Compiling $@\n"
	@mkdir -p bin
	@gcc -Wall -Wextra -pedantic -std=c99 -O2 -s $< -o $@

bin/bmi: src/bmi.c
	@printf "Compiling $@\n"
	@mkdir -p bin
	@gcc -Wall -Wextra -pedantic -std=c99 -O2 -s $< -o $@

bin/fire: src/fire.cpp
	@printf "Compiling $@\n"
	@mkdir -p bin
	@g++ -Wall -Wextra -pedantic -std=c++14 -O2 `sdl-config --cflags` $< -o $@ `sdl-config --libs`

bin/vigenere: src/vigenere.cpp
	@printf "Compiling $@\n"
	@mkdir -p bin
	@g++ -Wall -Wextra -pedantic -std=c++98 -O2 $< -o $@

bin/pdfcompress: src/pdfcompress.sh
	@printf "Copying $@\n"
	@mkdir -p bin
	@cp $< $@
	@chmod +x $@

bin/autoclick: src/autoclick.py
	@printf "Copying $@\n"
	@mkdir -p bin
	@cp $< $@
	@chmod +x $@

bin/hexstrdump: src/hexstrdump.c
	@printf "Compiling $@\n"
	@mkdir -p bin
	@gcc -Wall -Wextra -pedantic -std=c99 -O2 -s $< -o $@

bin/htmlm: src/htmlm.py
	@printf "Copying $@\n"
	@mkdir -p bin
	@cp $< $@
	@chmod +x $@
