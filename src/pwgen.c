#include <ctype.h>
#include <fcntl.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static const char warn_short_pw[] =
    "warning: passwords shorter than 16 characters are considered insecure\n";

static const char warn_no_numbers[] =
    "warning: passwords without numbers are considered insecure\n";

static const char warn_no_lowercase[] =
    "warning: passwords without lowercase letters are considered insecure\n";

static const char err_fd_urandom[] =
    "error: can't get file descriptor for urandom device\n";

static const char err_memory_alloc[] =
    "error: can't allocate memory on the heap\n";

static const char err_deadlock[] =
    "error: no possible characters left, try excluding less\n";

static const char info_help_message[] =
    "usage: pwgen [OPTIONS]\n"
    "Generate passwords with specified complexity.\n"
    "\n"
    "  -nN        generate N passwords\n"
    "  -lN        generated passwords are N characters long\n"
    "  -L         exclude lowercase characters\n"
    "  -N         exclude numbers\n"
    "  -S         exclude special characters\n"
    "  -W         disable warnings for weak passwords\n"
    "  -H, -h     show this help and don't generate any passwords\n"
    "  -E=[chars] exclude the given characters from generated passwords\n"
    "\n"
    "Warnings are issued for weak passwords, if the specified length\n"
    "is smaller than 16 characters, or if lowercase characters and/or \n"
    "numbers are excluded from the passwords.\n"
    "\n"
    "By default, one password is generated, which is 16 characters\n"
    "long, and includes all possible character types.";

typedef void * (*memset_ptr)(void *, int, size_t);

typedef struct {
    size_t length;
    size_t amount;
    bool has_specials;
    bool has_numbers;
    bool has_lowercase;
    bool no_warning;
    bool show_help;
    char *excluded;
} env_t;

static env_t process_params(int argc, char **argv);
static bool is_valid(char c, const env_t *flags);
static bool test_deadlock(const env_t *flags);

int main(int argc, char **argv) {
    env_t environment = process_params(--argc, ++argv);

    if (environment.show_help) {
        puts(info_help_message);
        return EXIT_SUCCESS;
    }

    if (test_deadlock (&environment)) {
        fputs(err_deadlock, stderr);
        free(environment.excluded);
        return EXIT_FAILURE;
    }

    if (!environment.no_warning) {
        if (environment.length < 16)
            fputs(warn_short_pw, stderr);

        if (!environment.has_numbers)
            fputs(warn_no_numbers, stderr);

        if (!environment.has_lowercase)
            fputs(warn_no_lowercase, stderr);
    }

    int urandom = open("/dev/urandom", O_RDONLY);
    if (urandom == -1) {
        fputs(err_fd_urandom, stderr);
        return EXIT_FAILURE;
    }


    char* buffer = (char *) malloc(environment.length + 1);
    if (buffer == NULL) {
        fputs(err_memory_alloc, stderr);
        close(urandom);
        return EXIT_FAILURE;
    }

    buffer[environment.length] = '\0';
    for (size_t a = 0; a < environment.amount; ++a) {
        for (size_t l = 0; l < environment.length; ++l) {
            char current;
            int n = 0;
            do {
                n = read(urandom, &current, 1);
                current = current % 255;
            } while (n != 1 || !is_valid(current, &environment));
            buffer[l] = current;
        }

        puts(buffer);
    }

    close(urandom);
    volatile memset_ptr memset_noopt = memset;
    memset_noopt(buffer, 0, environment.length);
    if (environment.excluded != NULL)
        free(environment.excluded);
    free(buffer);
    return EXIT_SUCCESS;
}

static env_t process_params(int argc, char **argv) {
    env_t result = {
        .length = 16,
        .amount = 1,
        .has_specials = true,
        .has_numbers = true,
        .has_lowercase = true,
        .no_warning = false,
        .show_help = false,
        .excluded = NULL
    };

    if (argv == NULL)
        return result;

    for (int i = 0; i < argc; ++i) {
        if (argv[i] == NULL || argv[i][0] != '-')
            continue;

        switch (argv[i][1]) {
            case 'n':
            case 'l':
                {
                    size_t * const env = (argv[i][1] == 'n') ? &result.amount
                                                             : &result.length;
                    const int len = strlen(argv[i]);
                    for (int j = 2; j < len; ++j) {
                        argv[i][j - 2] = argv[i][j];
                    }
                    argv[i][len - 2] = '\0';

                    *env = (size_t) atoi(argv[i]);
                }
                break;

            case 'E':
                {
                    if (argv[i][2] != '=')
                        continue;

                    const char *exc = argv[i] + 3;
                    if (result.excluded == NULL) {
                        size_t len = strlen(exc) + 1;
                        result.excluded = (char *) malloc(len);
                        strcpy(result.excluded, exc);
                    } else {
                        char *old = result.excluded;
                        size_t len = strlen(exc) +
                                     strlen(result.excluded) + 1;
                        result.excluded = (char *) malloc(len);
                        strcpy(result.excluded, old);
                        free(old);
                        strcat(result.excluded, exc);
                    }
                }
                break;

            default:
                {
                    for (size_t n = 1; n < strlen(argv[i]); ++n) {
                        #define handle_flag(ch, name, val) \
                            if (argv[i][n] == ch) result.name = val

                        handle_flag('L', has_lowercase, false);
                        handle_flag('N', has_numbers, false);
                        handle_flag('S', has_specials, false);
                        handle_flag('W', no_warning, true);

                        handle_flag('H', show_help, true);
                        handle_flag('h', show_help, true);

                        #undef handle_flag
                    }
                }
                break;
        }
    }

    return result;
}

static bool is_valid(char c, const env_t *flags) {
    const int cc = c;

    if (!isprint(cc) || !isgraph(cc) || iscntrl(cc))
        return false;

    if (!flags->has_numbers && isdigit(cc))
        return false;

    if (!flags->has_lowercase && isalpha(cc) && islower(cc))
        return false;

    if (!flags->has_specials && !isalnum(cc))
        return false;

    if (flags->excluded != NULL) {
        for (unsigned i = 0; i < strlen(flags->excluded); ++i) {
            if (c == flags->excluded[i])
                return false;
        }
    }

    return true;
}

static bool test_deadlock(const env_t *flags) {
    if (flags->excluded != NULL) {
        bool deadlock = true;
        for (int i = 0; i < 256; ++i) {
            if (is_valid ((char) i, flags)) {
                deadlock = false;
                break;
            }
        }
        return deadlock;
    }

    return false;
}
