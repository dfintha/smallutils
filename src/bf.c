#include <stdio.h>
#include <string.h>

static char * flookup(char *ip) {
    unsigned count = 0;
    for (++ip; !(*ip == ']' && count == 0); ++ip) {
        if (*ip == '[') ++count;
        if (*ip == ']') --count;
    }
    return ip;
}

static char * blookup(char *ip) {
    unsigned count = 0;
    for (--ip; !(*ip == '[' && count == 0); --ip) {
        if (*ip == ']') ++count;
        if (*ip == '[') --count;
    }
    return ip;
}

static void cread(char *code) {
    int current;
    memset(code, 0x00, 30000);
    while ((current = getchar()) != EOF)
        *code++ = current;
}

int main(void) {
    char code[30000], *ip = code;
    char data[30000], *dp = data;
    memset(data, 0x00, 30000);
    cread(code);

    while (*ip != '\0') {
        switch (*ip) {
            case '>':
                ++dp, ++ip;
                break;
            case '<':
                --dp, ++ip;
                break;
            case '+':
                ++(*dp), ++ip;
                break;
            case '-':
                --(*dp), ++ip;
                break;
            case '.':
                putchar(*dp), ++ip;
                break;
            case ',':
                *dp = getchar(), ++ip;
                break;
            case '[':
                ip = (*dp == 0) ? flookup(ip) : ip + 1;
                break;
            case ']':
                ip = (*dp != 0) ? blookup(ip) : ip + 1;
                break;
            default:
                ++ip;
                break;
        }
    }

    return 0;
}
