
# https://stackoverflow.com/questions/42014594/linear-scaling-between-2-font-sizes-using-calc-and-vw#42019122

## attempt to make some sense of these numbers in R
#
# df <- data.frame(size=c(20, 30, 40), val=c(192.0, 128.0, 96.0))
# lm(formula = val ~ poly(size, degree=2), data = df)
#
# Coefficients:
#    (Intercept)  poly(size, degree = 2)1  poly(size, degree = 2)2
#         138.67                   -67.88                    13.06
#
# df2 <- data.frame(size=c(20, 30, 40), val=c(49.1, 33.8, 25.0))
# lm(formula = val ~ poly(size, degree=2), data = df2)
#
# Coefficients:
#    (Intercept)  poly(size, degree = 2)1  poly(size, degree = 2)2
#         35.967                  -17.041                    2.654

class Font:
    # mono fonts only, ratios.
    _config = {"Inconsolata-Regular": {
        "20": (192.0, 49.1), # line length, height
        "30": (128.0, 33.8),
        "40": (96.0, 25.0),
        "dir": "codeface/fonts/inconsolata"},
    "ProggyClean": {
        "20": (213.5, 63.6),
        "30": (147.5, 43.3),
        "40": (106.6, 32.7),
        "dir": "codeface/fonts/proggy-clean"},
    "SourceCodePro-Regular": {
        "20": (160.0, 41.4),
        "30": (106.5, 27.7),
        "40": (80.0, 21.0),
        "dir": "codeface/fonts/source-code-pro"
    }}
    @staticmethod
    def file_for(name="Inconsolata-Regular"):
        return Font._config[name]['dir'] + "/" + name + ".ttf"

    def __init__(self, **kwargs):
         self.set_font(**kwargs)

    def set_font(self, name=None, size=None):
        if name is not None:
            self.name = name
        if size is not None:
            self.size = size

    def get_file(self):
        return Font.file_for(self.name)

    @property
    def max_char_per_line(self):
        return Font._config[self.name][str(self.size)][0]

    @property
    def max_lines_per_screen(self):
        return Font._config[self.name][str(self.size)][1]

    @property
    def max_lines(self):
        return int(self.max_lines_per_screen)

    @property
    def half_a_screen(self):
        return int(self.max_lines_per_screen/2)
