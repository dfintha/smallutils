BINARIES= \
	bin/bf \
	bin/pwgen \
	bin/bmi

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
