#include <stdio.h>
#include <stdint.h>

static char * byte2hex(uint8_t byte, char *output) {
    static const char *digits = "0123456789ABCDEF";
    output[0] = '\\';
    output[1] = 'x';
    output[3] = digits[byte % 16];
    byte /= 16;
    output[2] = digits[byte % 16];
    output[4] = '\0';
    return output;
}

static void process_single_file(const char *path) {
    FILE *handle = fopen(path, "rb");
    if (!handle) {
        fprintf(stderr, "failed to open file: '%s'\n", path);
        return;
    }

    fseek(handle, 0, SEEK_END);
    const size_t length = ftell(handle);
    fseek(handle, 0, SEEK_SET);

    static const size_t chunk_size = 8;
    const size_t chunks = length / chunk_size;

    char buffer[5] = { '\0', '\0', '\0', '\0', '\0' };
    for (size_t i = 0; i <= chunks; ++i) {
        const size_t current_length = (i == chunks) ? length % chunk_size : chunk_size;
        uint8_t current[8];
        if (fread(current, 1, current_length, handle) != current_length) {
            fprintf(stderr, "\nFailed to load file contents, exiting.\n");
            return;
        }
        for (size_t j = 0; j < current_length; ++j) {
            fputs(byte2hex(current[j], buffer), stdout);
        }
    }

    fputc('\n', stdout);
    fclose(handle);
}

int main(int argc, char **argv) {
    --argc, ++argv;
    for (int i = 0; i < argc; ++i) {
        process_single_file(argv[i]);
    }
    return 0;
}
