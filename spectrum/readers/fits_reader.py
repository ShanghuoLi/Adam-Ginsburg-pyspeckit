import pyfits
import spectrum.units as units
import numpy.ma as ma
import numpy as np
from . import make_axis

def open_1d_fits(filename,specnum=0,wcstype='',errspecnum=None,**kwargs):
    """
    Grabs all the relevant pieces of a simple FITS-compliant 1d spectrum

    Inputs:
        wcstype - the suffix on the WCS type to get to
            velocity/frequency/whatever
        specnum - Which # spectrum, along the y-axis, is 
            the data?
        errspecnum - Which # spectrum, along the y-axis,
            is the error spectrum?

    """
    f = pyfits.open(filename)
    hdr = f[0].header

    if hdr.get('NAXIS') == 2:
        if isinstance(specnum,list):
            # allow averaging of multiple spectra (this should be modified
            # - each spectrum should be a Spectrum instance)
            spec = ma.array(f[0].data[specnum,:]).mean(axis=0)
        elif isinstance(specnum,int):
            spec = ma.array(f[0].data[specnum,:]).squeeze()
        else:
            raise TypeError("Specnum is of wrong type (not a list of integers or an integer).  Type: %s" %
                    str(type(specnum)))
        if errspecnum is not None:
            errspec = ma.array(f[0].data[errspecnum,:]).squeeze()
        else:
            errspec = spec*0 # set error spectrum to zero if it's not in the data

    elif hdr.get('NAXIS') > 2:
        for ii in xrange(2,hdr.get('NAXIS')):
            # only fail if extra axes have more than one row
            if hdr.get('NAXIS%i' % ii) > 1:
                raise ValueError("Too many axes for open_1d_fits")
        spec = ma.array(f[0].data).squeeze()
        if errspecnum is None: errspec = spec*0 # set error spectrum to zero if it's not in the data
    else:
        spec = ma.array(f[0].data).squeeze()
        if errspecnum is None: errspec = spec*0 # set error spectrum to zero if it's not in the data

    if hdr.get('ORIGIN') == 'CLASS-Grenoble':
        # Use the CLASS FITS definition (which is non-standard)
        # http://iram.fr/IRAMFR/GILDAS/doc/html/class-html/node84.html
        # F(n) = RESTFREQ + CRVALi + ( n - CRPIXi ) * CDELTi
        print "Loading a CLASS .fits spectrum"
        dv = -1*hdr.get('CDELT1')
        v0 = hdr.get('RESTFREQ') + hdr.get('CRVAL1')
        p3 = hdr.get('CRPIX1')
    elif hdr.get('CD1_1'+wcstype):
        dv,v0,p3 = hdr['CD1_1'+wcstype],hdr['CRVAL1'+wcstype],hdr['CRPIX1'+wcstype]
        hdr.update('CDELT1',dv)
    else:
        dv,v0,p3 = hdr['CDELT1'+wcstype],hdr['CRVAL1'+wcstype],hdr['CRPIX1'+wcstype]

    # Deal with logarithmic wavelength binning if necessary
    if hdr.get('WFITTYPE') == 'LOG-LINEAR':
        xconv = lambda v: 10**((v-p3+1)*dv+v0)
        xarr = xconv(np.arange(len(spec)))
    else:
        xconv = lambda v: ((v-p3+1)*dv+v0)
        xarr = xconv(np.arange(len(spec)))

    XAxis = make_axis(xarr,hdr,wcstype=wcstype,**kwargs)

    return spec,errspec,XAxis,hdr

