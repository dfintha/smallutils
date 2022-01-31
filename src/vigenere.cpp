#include <cctype>
#include <cstring>
#include <iostream>

static char add(char lhs, char rhs) {
    return ((lhs - 'A' + rhs - 'A') % 26) + 'A';
}

static char subtract(char lhs, char rhs) {
    return ((lhs - 'A' - rhs + 'A' + 52) % 26) + 'A';
}

int main(int argc, char **argv) {
    --argc, ++argv;
    if (argc != 2) {
        std::cerr << "usage: vigenere <encrypt|decrypt> <key>" << std::endl;
        return 1;
    }

    char *key = argv[1];
    const size_t key_length = strlen(key);
    for (size_t i = 0; i < key_length; ++i)
        key[i] = toupper(key[i]);

    enum {
        encrypt_mode,
        decrypt_mode
    } mode;

    if (strcmp(argv[0], "encrypt") == 0) {
        mode = encrypt_mode;
    } else if (strcmp(argv[0], "decrypt") == 0) {
        mode = decrypt_mode;
    } else {
        std::cerr << "mode must be either 'encrypt' or 'decrypt'" << std::endl;
        return 1;
    }

    char current;
    size_t position = 0;
    while (std::cin.get(current)) {
        if (!isalpha(current)) {
            std::cout.put(current);
        } else {
            current = toupper(current);
            if (mode == encrypt_mode) {
                std::cout.put(add(current, key[position++ % key_length]));
            } else {
                std::cout.put(subtract(current, key[position++ % key_length]));
            }
        }
    }

    return 0;
}
