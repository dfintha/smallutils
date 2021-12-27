#include <math.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef enum { CM, IN } height_unit_t;
typedef enum { KG, LB } mass_unit_t;

typedef enum {
    very_severely_underweight,
    severely_underweight,
    underweight,
    normal_weight,
    overweight,
    moderately_obese,
    severely_obese,
    very_severely_obese
} mass_index_classification;

static bool query(double *height, height_unit_t *height_unit, double *mass, mass_unit_t *mass_unit) {
    char buffer[3];

    printf("Please enter your height in '[amount] [cm|in]' format!\n");
    int read = scanf("%lf %2s", height, buffer);
    if (read != 2) {
        fprintf(stderr, "Error: Invalid height format!\n");
        return false;
    } else if (strcmp(buffer, "cm") == 0) {
        *height_unit = CM;
    } else if (strcmp(buffer, "in") == 0) {
        *height_unit = IN;
    } else {
        fprintf(stderr, "Error: Invalid height format!\n");
        return false;
    }

    printf("Please enter your mass in '[amount] [kg|lb]' format!\n");
    read = scanf("%lf %2s", mass, buffer);
    if (read != 2) {
        fprintf(stderr, "Error: Invalid mass format!\n");
        return false;
    } else if (strcmp(buffer, "kg") == 0) {
        *mass_unit = KG;
    } else if (strcmp(buffer, "lb") == 0) {
        *mass_unit = LB;
    } else {
        fprintf(stderr, "Error: Invalid mass format!\n");
        return false;
    }

    return true;
}

static double calculate(double height, height_unit_t height_unit, double mass, mass_unit_t mass_unit) {
    static const double inch_to_cm = 2.5400;
    static const double lbs_to_kg = 0.4536;
    const double height_cm = (height_unit == CM) ? height : height * inch_to_cm;
    const double height_m = height_cm / 100;
    const double mass_kg = (mass_unit == KG) ? mass : mass * lbs_to_kg;
    return mass_kg / pow(height_m, 2);
}

static mass_index_classification classify(double bmi) {
    if (bmi < 15) return very_severely_underweight;
    if (bmi < 16) return severely_underweight;
    if (bmi < 18.5) return underweight;
    if (bmi < 25) return normal_weight;
    if (bmi < 30) return overweight;
    if (bmi < 35) return moderately_obese;
    if (bmi < 40) return severely_obese;
    return very_severely_obese;
}

int main(void) {
    double height;
    height_unit_t height_unit;
    double mass;
    mass_unit_t mass_unit;

    if (!query(&height, &height_unit, &mass, &mass_unit))
        return EXIT_FAILURE;

    const double bmi = calculate(height, height_unit, mass, mass_unit);
    const mass_index_classification classification = classify(bmi);

    printf("Your BMI score is %.2lf. You are ", bmi);
    switch (classification) {
        case very_severely_underweight:
            printf("very severely underweight.\n");
            break;
        case severely_underweight:
            printf("severely underweight.\n");
            break;
        case underweight:
            printf("underweight.\n");
            break;
        case normal_weight:
            printf("normal weight.\n");
            break;
        case overweight:
            printf("overweight.\n");
            break;
        case moderately_obese:
            printf("moderately obese (class I).\n");
            break;
        case severely_obese:
            printf("severely obese (class II).\n");
            break;
        case very_severely_obese:
            printf("very severely obese (class III).\n");
            break;
        default:
            printf("in an invalid index range.\n");
            break;
    }

    return EXIT_SUCCESS;
}
