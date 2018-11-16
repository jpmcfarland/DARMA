"""Genenerate artificial data.
"""

__version__ = '@(#)$Revision$'

import math

from .common import Array, Arrayrandom
from .common import DARMAError, _HAS_NUMPY
from .image import image


class image_generator:

    """
       Provides object capable of producing artificially generated data with
       various properties.
    """

    def __init__(self, xsize, ysize):
        """
           Constructor

           xsize -- the x dimension of the generated images
           ysize -- the y dimension of the generated images
        """

        # Allow DARMA to be imported even if NumPy is not available.
        if not _HAS_NUMPY:
            raise DARMAError('DARMA pixel functionality not possible: cannot import module numpy')

        self.xsize = xsize
        self.ysize = ysize

    ##########################################################################
    #
    # Noise images
    #

    def generate_random_floats(self):
        """
           Generate an image with noise uniformly distributed between min_pix
           and max_pix.
        """

        # PyFITS Array axes are reversed.
        return image(data=Arrayrandom.random([self.ysize, self.xsize]))

    def generate_random_uniform(self, min_pix=0.0, max_pix=1.0):
        """
           Generate an image with noise uniformly distributed between min_pix
           and max_pix.
        """

        # PyFITS Array axes are reversed.
        return image(data=Arrayrandom.uniform(min_pix, max_pix,
                                              [self.ysize, self.xsize]))

    def generate_random_ints(self, min_pix=0, max_pix=10):
        """
           Generate an image with noise uniformly distributed between min_pix
           and max_pix.
        """

        # PyFITS Array axes are reversed.
        return image(data=Arrayrandom.randint(min_pix, max_pix,
                                              [self.ysize, self.xsize]))

    def generate_random_beta(self, a=1.0, b=1.0):
        """
           Generate an image with noise in a Beta distribution with parameters
           alpha (a) and beta (b).  alpha or beta should not be 0.
        """

        if a == 0 or b == 0:
            raise DARMAError('Neither a nor b can be 0 in the Beta function!')
        # PyFITS Array axes are reversed.
        return image(data=Arrayrandom.beta(a, b, [self.ysize, self.xsize]))

    def generate_random_chi_square(self, df=10):
        """
           Generate an image with noise in a chi^2 distribution with df degrees
           of freedom.
        """

        # PyFITS Array axes are reversed.
        return image(data=Arrayrandom.chi_square(df, [self.ysize, self.xsize]))

    def generate_random_exponential(self, mean=10.0):
        """
           Generate an image with noise exponentially distributed around a
           mean.
        """

        # PyFITS Array axes are reversed.
        return image(data=Arrayrandom.exponential(mean, [self.ysize,
                                                         self.xsize]))

    def generate_random_F(self, dfn=10, dfd=10):
        """
           Generate an image with noise in an F distribution with dfn degrees
           of freedom in the numerator and dfd degrees of freedom in the
           denominator.
        """

        # PyFITS Array axes are reversed.
        return image(data=Arrayrandom.f(dfn, dfd, [self.ysize, self.xsize]))

    def generate_random_gamma(self, a=0.0, r=1):
        """
           Generate an image with noise in a beta distribution with location
           parameter a and distribution shape parameter r.
        """

        # PyFITS Array axes are reversed.
        return image(data=Arrayrandom.gamma(a, r, [self.ysize, self.xsize]))

    def generate_random_gauss(self, dispersion=1.0, mean=0.0):
        """
           Generate an image with noise distributed normally around mean, with
           rms dispersion.
        """

        # PyFITS Array axes are reversed.
        return image(data=Arrayrandom.normal(mean, dispersion,
                                             [self.ysize, self.xsize]))

    def generate_random_lorentz(self, dispersion=1.0, mean=0.0):
        """
           Generate an image with lorentzian distributed noise.
        """

        # The ratio of two normally distributed random variables has a Cauchy
        # (Lorentzian) distrubution (see Hodgson's paradox).
        # PyFITS Array axes are reversed.
        X = Arrayrandom.normal(mean, dispersion, [self.ysize, self.xsize])
        Y = Arrayrandom.normal(mean, dispersion, [self.ysize, self.xsize])

        return image(data=X / Y)

    def generate_random_binomial(self, trials=10, p=0.1):
        """
           Generate an image with binomially distributed noise.
        """

        # PyFITS Array axes are reversed.
        return image(data=Arrayrandom.binomial(trials, p, [self.ysize,
                                                           self.xsize]))

    def generate_random_poisson(self, mean=10.0):
        """
           Generate an image with noise Poisson distributed around a mean
        """

        # PyFITS Array axes are reversed.
        return image(data=Arrayrandom.poisson(mean, [self.ysize, self.xsize]))

    ##########################################################################
    #
    # Function images
    #

    def generate_poly2d(self, c=0.0, c_x=0.0, c_y=0.0, c_xx=0.0, c_xy=0.0,
                        c_yy=0.0):
        """
           Generate an image from a 2d polynomial.

           ima(x,y) = c+c_x*x+c_y*y+c_xx*x*x+c_xy*x*y+c_yy*y*y
        """
        def poly2d(y, x):
            return c + c_x * x + c_y * y + c_xx * x * x + c_xy * x * y + c_yy * y * y

        # PyFITS Array axes are reversed.
        return image(data=Array.fromfunction(poly2d, (self.ysize, self.xsize)))

    def generate_gauss2d(self, amplitude=1.0, x_pos=None, y_pos=None,
                         sigma_x=1.0, sigma_y=1.0, param_dict=None):
        """
           Generate an image from a 2d Gaussian function.

           ima(x,y) = amplitude*exp{-0.5*[((x-x_pos)/sigma_x)**2 +
                                          ((y-y_pos)/sigma_y)**2]}

           If x_pos or y_pos are not given, they default to center of the
           respective axis.

           An arbitrary number of Gaussian functions can be plotted at once
           using a parameter dictionary.  If param_dict is given, it overrides
           all other parameters and should specify one or more Gaussian
           function paramter sets.  All keys MUST exist in the dictionary and
           all values MUST be same length iterable (list or tuple), where the
           length indicates the number of functions desired.  The param_dict
           has this structure:

           param_dict = {'amplitude' : [],
                         'x_pos'     : [],
                         'y_pos'     : [],
                         'sigma_x'   : [],
                         'sigma_y'   : []}
        """

        if param_dict is None:
            if x_pos is None:
                x_pos = self.xsize / 2.0
            if y_pos is None:
                y_pos = self.ysize / 2.0
            pars = {'amplitude': [amplitude],
                    'x_pos': [x_pos],
                    'y_pos': [y_pos],
                    'sigma_x': [sigma_x],
                    'sigma_y': [sigma_y]}
        else:
            pars = param_dict

        if not (len(pars['x_pos']) == len(pars['y_pos']) == len(pars['amplitude']) == len(pars['sigma_x']) == len(pars['sigma_y'])):
            raise DARMAError('param_dict values of different length!')

        def gauss2d(y, x):
            return ampl * math.e**(-0.5 * (((x - xpos - 1) / sigx)**2 + ((y - ypos - 1) / sigy)**2))

        ampl = pars['amplitude'][0]
        xpos = pars['x_pos'][0]
        ypos = pars['y_pos'][0]
        sigx = pars['sigma_x'][0]
        sigy = pars['sigma_y'][0]
        # PyFITS Array axes are reversed.
        data = Array.fromfunction(gauss2d, (self.ysize, self.xsize))

        if len(pars['x_pos']) > 1:
            for i in range(1, len(pars['x_pos'])):
                ampl = pars['amplitude'][i]
                xpos = pars['x_pos'][i]
                ypos = pars['y_pos'][i]
                sigx = pars['sigma_x'][i]
                sigy = pars['sigma_y'][i]
                # PyFITS Array axes are reversed.
                data += Array.fromfunction(gauss2d, (self.ysize, self.xsize))

        return image(data=data)

    def generate_lowpass(self, sigma_x=1.0, sigma_y=1.0):
        """
           Generate a low-pass filter image.  Construct a 2-Dim Gaussian
           function and move the center to the corners.
        """

        data = self.generate_gauss2d(sigma_x=sigma_x, sigma_y=sigma_y).data
        newdata = Array.empty(shape=data.shape, dtype=data.dtype)  # unitialized

        # PyFITS Array axes are reversed.
        if self.ysize % 2:
            x0 = self.ysize / 2
        else:
            x0 = self.ysize / 2 - 1
        if self.xsize % 2:
            y0 = self.xsize / 2
        else:
            y0 = self.xsize / 2 - 1
        x1 = self.ysize
        y1 = self.xsize

        newdata[0:x0, 0:y0] = data[0:x0, 0:y0][::-1, ::-1]
        newdata[x0:x1, 0:y0] = data[x0:x1, 0:y0][::-1, ::-1]
        newdata[0:x0, y0:y1] = data[0:x0, y0:y1][::-1, ::-1]
        newdata[x0:x1, y0:y1] = data[x0:x1, y0:y1][::-1, ::-1]

        return image(data=newdata)

    def generate_lorentz2d(self, amplitude=1.0, x_pos=None, y_pos=None,
                           sigma_x=1.0, sigma_y=1.0, param_dict=None):
        """
           Generate an image from a 2d Lorentzian function.

           ima(x,y) = amplitude*((sigx/((x-xpos-1)**2+sigx**2)) *
                                 (sigy/((y-ypos-1)**2+sigy**2)))
           If x_pos or y_pos are not given, they default to center of the
           respective axis.

           An arbitrary number of Lorentzian functions can be plotted at once
           using a parameter dictionary.  If param_dict is given, it overrides
           all other parameters and should specify one or more Lorentzian
           function paramter sets.  All keys MUST exist in the dictionary and
           all values MUST be same length iterable (list or tuple), where the
           length indicates the number of functions desired.  The param_dict
           has this structure:

           param_dict = {'amplitude' : [],
                         'x_pos'     : [],
                         'y_pos'     : [],
                         'sigma_x'   : [],
                         'sigma_y'   : []}
        """

        if param_dict is None:
            if x_pos is None:
                x_pos = self.xsize / 2.0
            if y_pos is None:
                y_pos = self.ysize / 2.0
            pars = {'amplitude': [amplitude],
                    'x_pos': [x_pos],
                    'y_pos': [y_pos],
                    'sigma_x': [sigma_x],
                    'sigma_y': [sigma_y]}
        else:
            pars = param_dict

        if not (len(pars['x_pos']) == len(pars['y_pos']) == len(pars['amplitude']) == len(pars['sigma_x']) == len(pars['sigma_y'])):
            raise DARMAError('param_dict values of different length!')

        def lorentz2d(y, x):
            return ampl * ((sigx / ((x - xpos - 1)**2 + sigx**2)) * (sigy / ((y - ypos - 1)**2 + sigy**2)))

        ampl = pars['amplitude'][0]
        xpos = pars['x_pos'][0]
        ypos = pars['y_pos'][0]
        sigx = pars['sigma_x'][0]
        sigy = pars['sigma_y'][0]
        # PyFITS Array axes are reversed.
        data = Array.fromfunction(lorentz2d, (self.ysize, self.xsize))

        if len(pars['x_pos']) > 1:
            for i in range(1, len(pars['x_pos'])):
                ampl = pars['amplitude'][i]
                xpos = pars['x_pos'][i]
                ypos = pars['y_pos'][i]
                sigx = pars['sigma_x'][i]
                sigy = pars['sigma_y'][i]
                # PyFITS Array axes are reversed.
                data += Array.fromfunction(lorentz2d, (self.ysize, self.xsize))

        return image(data=data)
