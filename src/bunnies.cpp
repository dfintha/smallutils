#include <chrono>
#include <curses.h>
#include <iostream>
#include <locale.h>
#include <thread>

#define HEART_COLOR 1
#define BUNNIES_COLOR 2

static const char *bunnies =
    "                              ▓▓▓▓▓▓    ▓▓▓▓▓▓                                                    ▓▓▓▓▓▓    ▓▓▓▓▓▓\n"
    "                            ▓▓      ▓▓▓▓      ▓▓                                                ▓▓░░░░░░▓▓▓▓░░░░░░▓▓\n"
    "                            ▓▓░░      ▓▓      ▓▓                                                ▓▓░░░░░░▓▓░░░░░░██▓▓\n"
    "                            ▓▓░░░░    ▓▓        ▓▓                                            ▓▓░░░░░░░░▓▓░░░░████▓▓\n"
    "                              ▓▓░░░░    ▓▓      ▓▓                                            ▓▓░░░░░░▓▓░░░░████▓▓\n"
    "                              ▓▓░░░░    ▓▓      ▓▓                                            ▓▓░░░░░░▓▓░░░░████▓▓\n"
    "                                ▓▓░░░░    ▓▓      ▓▓                                        ▓▓░░░░░░▓▓░░░░████▓▓\n"
    "                                ▓▓░░░░    ▓▓      ▓▓                                        ▓▓░░░░░░▓▓░░░░████▓▓\n"
    "                                  ▓▓░░░░    ▓▓    ▓▓                                        ▓▓░░░░▓▓░░░░████▓▓\n"
    "                                  ▓▓░░░░    ▓▓    ░░▓▓                                    ▓▓░░░░░░▓▓░░░░████▓▓\n"
    "                                    ▓▓░░░░    ▓▓▓▓    ▓▓▓▓                            ▓▓▓▓░░░░▓▓▓▓░░░░████▓▓\n"
    "                                    ▓▓░░░░                ▓▓                        ▓▓░░░░░░░░░░░░░░░░████▓▓\n"
    "                ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓      ▓▓                    ▓▓                    ▓▓░░░░░░░░░░░░░░░░░░░░▓▓      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n"
    "            ▓▓▓▓                ▓▓▓▓  ▓▓                      ▓▓                ▓▓░░░░░░░░░░░░░░░░░░░░░░▓▓  ▓▓▓▓░░░░░░░░░░░░░░░░▓▓▓▓\n"
    "          ▓▓                        ▓▓              ████      ▓▓                ▓▓░░░░░░░████░░░░░░░░░░░░░▓▓░░░░░░░░░░░░░░░░░░░░░░░░▓▓\n"
    "        ▓▓                                          ████        ▓▓            ▓▓░░░░░░░░░████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓\n"
    "      ▓▓                                                      ░░▓▓            ▓▓░░▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓\n"
    "    ▓▓                                                          ▓▓            ▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓\n"
    "    ▓▓                                                          ▓▓            ▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓\n"
    "  ▓▓                                        ░░              ▓▓▓▓                ▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓\n"
    "  ▓▓                                          ░░░░░░░░▓▓▓▓▓▓                        ▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓\n"
    "  ▓▓                                                ░░▓▓                                ▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓\n"
    "  ▓▓                                                ░░▓▓                                ▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓\n"
    "  ▓▓                                                ░░▓▓                                ▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓\n"
    "  ▓▓                                                ░░▓▓                                ▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓\n"
    "  ▓▓                                                ░░▓▓                                ▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓\n"
    "  ▓▓                                                ░░▓▓                                ▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓\n"
    "    ▓▓    ░░          ░░░░░░░░                      ░░▓▓                                ▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓\n"
    "    ▓▓      ░░        ▓▓▓▓▓▓▓▓░░              ▓▓  ░░▓▓                                    ▓▓░░░░▓▓░░░░░░░░░░░░░░░░▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░▓▓\n"
    "      ▓▓    ░░                ▓▓░░            ▓▓░░░░▓▓                                    ▓▓░░░░▓▓░░░░░░░░░░░░░░▓▓░░░░░░░░░░░░░░░░░░░░░░▓▓\n"
    "        ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                                        ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n";

static const char *heart[] = {
    "          ",
    "          ",
    "▓▓▓▓  ▓▓▓▓",
    "▓▓▓▓▓▓▓▓▓▓",
    "  ▓▓▓▓▓▓  ",
    "    ▓▓    ",
    "          ",
    "          "
};

int main(void) {
    setlocale(LC_ALL, "");

    const WINDOW *terminal = initscr();
    if (has_colors() == TRUE) {
        start_color();
        use_default_colors();
        init_pair(HEART_COLOR, COLOR_RED, -1);
        init_pair(BUNNIES_COLOR, COLOR_WHITE, -1);
    }

    const int image_width = 144;
    const int image_height = 31;
    const int total_width = getmaxx(terminal);
    const int total_height = getmaxy(terminal);
    const int needed_width = image_width + 4;
    const int needed_height = total_height + 2;

    if (total_width < needed_width || total_height < image_height + 2) {
        endwin();
        std::cerr << "Terminal resolution needs to be larger or equal than "
                  << needed_width << 'x' << needed_height << '!'
                  << std::endl;
        return 1;
    }

    noecho();
    curs_set(0);
    const int left = (total_width - image_width) / 2;
    const int top = (total_height - image_height) / 2;
    WINDOW *window = newwin(image_height, image_width, top, left);

    bool even_frame = false;
    while (true) {
        const int top = even_frame ? 1 : 0;
        wattron(window, COLOR_PAIR(BUNNIES_COLOR));
        mvwprintw(window, 0, 0, "%s", bunnies);
        wattroff(window, COLOR_PAIR(BUNNIES_COLOR));
        for (int i = 0; i < 8; ++i) {
            wattron(window, COLOR_PAIR(HEART_COLOR));
            mvwprintw(window, top + i, 67, "%s", heart[i]);
            wattroff(window, COLOR_PAIR(HEART_COLOR));
        }
        refresh();
        wrefresh(window);
        even_frame = !even_frame;
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    endwin();
    return 0;
}
