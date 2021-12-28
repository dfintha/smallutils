#include <chrono>
#include <cstdint>
#include <iostream>
#include <memory>
#include <utility>

#include <SDL.h>

constexpr int scheme[] = { 0xFF, 0x55, 0x00 };

enum error_code {
    EXIT_SUCCESSFUL = 0,
    EXIT_SDL_INIT_FAILED = 1,
    EXIT_SDL_SURFACE_CREATION_FAILED = 2,
};

int width = 0;
int height = 0;
int scale = 0;
bool fullscreen = true;
std::unique_ptr<int[]> pixels;
std::unique_ptr<uint32_t[]> palette;

static void parse_arguments(int argc, char **argv) {
    enum parse_state {
        ARGUMENT,
        WIDTH,
        HEIGHT
    } state = ARGUMENT;

    --argc, ++argv;
    for (int i = 0; i < argc; ++i) {
        const char *arg = argv[i];
        switch (state) {
            case ARGUMENT:
                if (strcmp(arg, "--width") == 0) {
                    state = WIDTH;
                } else if (strcmp(arg, "--height") == 0) {
                    state = HEIGHT;
                } else if (strcmp(arg, "--no-full-screen") == 0) {
                    fullscreen = false;
                }
                break;
            case WIDTH:
                width = atoi(arg);
                state = ARGUMENT;
                break;
            case HEIGHT:
                height = atoi(arg);
                state = ARGUMENT;
                break;
            default:
                break;
        }
    }
}

static void query_max_resolution() {
    SDL_Rect **modes = SDL_ListModes(nullptr, SDL_FULLSCREEN | SDL_HWSURFACE);
    if (modes == nullptr || modes == reinterpret_cast<SDL_Rect **>(-1)) {
        std::cerr << "Warning: Could not get resolution, falling back to 640x480." << std::endl;
        width = 640;
        height = 480;
        return;
    }

    SDL_Rect *highest = nullptr;
    for (int i = 0; modes[i] != nullptr; ++i) {
        SDL_Rect *current = modes[i];
        const bool first = (highest == nullptr);
        if (first || ((current->w >= highest->w) && (current->h >= highest->h)))
            highest = current;
    }

    width = highest->w;
    height = highest->h;
}

static void initialize_animation(SDL_Surface *surface) {
    scale = height / 10;
    pixels = std::unique_ptr<int[]>(new int[width * height]);
    palette = std::unique_ptr<uint32_t[]>(new uint32_t[scale]);

    for (int i = 0; i < scale; ++i) {
        const uint8_t red = i * scheme[0] / scale;
        const uint8_t green = i * scheme[1] / scale;
        const uint8_t blue = i * scheme[2] / scale;
        palette[i] = SDL_MapRGB(surface->format, red, green, blue);
    }

    memset(pixels.get(), 0x00, width * height * sizeof(int));
    for (int i = 0; i < width; ++i)
        pixels[(height - 1) * width + i] = scale - 1;

    srand(unsigned(time(nullptr)));
}

static void render_frame(SDL_Surface *surface) {
    for (int x = 0; x < width; ++x) {
        for (int y = 1; y < height; ++y) {
            const int index = y * width + x;
            if (pixels[index] == 0) {
                pixels[index - width] = 0;
            } else {
                const int random = (rand() % 3) & 3;
                const int where = index - random + 1;
                pixels[where - width] = pixels[index] - (random & 1);
            }
        }
    }

    uint32_t *surface_pixels = static_cast<uint32_t *>(surface->pixels);
    for (int i = 0; i < width * height; ++i)
        surface_pixels[i] = palette[pixels[i]];
}

static void loop_animation(SDL_Surface *surface) {
    using clock = std::chrono::system_clock;
    using time = clock::time_point;
    constexpr auto delay = std::chrono::milliseconds(25);

    SDL_Event event;

    bool exiting = false;
    time before = clock::now();

    while (!exiting) {
        time now = clock::now();
        if (now - before > delay) {
            render_frame(surface);
            SDL_Flip(surface);
            before = now;
        }

        if (!SDL_PollEvent(&event))
            continue;

        if (event.type == SDL_QUIT)
            exiting = true;

        if (event.type == SDL_KEYDOWN && event.key.keysym.sym == SDLK_q)
            exiting = true;
    }
}

int main(int argc, char **argv) {
    parse_arguments(argc, argv);

    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        std::cerr << "Error: Could not initialize SDL." << std::endl;
        return EXIT_SDL_INIT_FAILED;
    }

    if (width == 0 && height == 0)
        query_max_resolution();

    SDL_Surface *surface = SDL_SetVideoMode(width, height, 32, SDL_SWSURFACE);
    if (surface == nullptr) {
        std::cerr << "Error: Could not create an SDL surface." << std::endl;
        return EXIT_SDL_SURFACE_CREATION_FAILED;
    }

    SDL_WM_SetCaption("Fire", nullptr);
    if (fullscreen)
        SDL_WM_ToggleFullScreen(surface);

    initialize_animation(surface);

    SDL_ShowCursor(SDL_DISABLE);
    loop_animation(surface);
    SDL_ShowCursor(SDL_ENABLE);

    SDL_Quit();
    return EXIT_SUCCESSFUL;
}
