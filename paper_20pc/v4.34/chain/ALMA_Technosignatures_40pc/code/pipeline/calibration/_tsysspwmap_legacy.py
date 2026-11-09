# Ported from the canonical NRAO/CASA source
# (casa/gcwrap/python/scripts/recipes/almahelpers.py, radio-astro/casa on
# GitHub), which is not importable in this modern CASA 6.x environment
# (no 'casarecipes'/'recipes' package installed). Only the one function
# actually needed (tsysspwmap) is ported, with taskinit.tbtool() replaced
# by the modern casatools.table() -- identical open/getcol/close API, no
# other logic changed. Verified against real archival data (Wolf 219,
# 2015.1.00783.S) before being trusted for calibration replay.
import numpy as np
from casatools import table as _tbtool


class _SpwMap:
    def __init__(self, calSpwId):
        self.calSpwId = calSpwId
        self.validFreqRange = []
        self.mapsToSpw = []
        self.bbNo = None


class _SpwInfo:
    def __init__(self, msfile, spwId):
        self.tb = _tbtool()
        self.tableName = "%s/SPECTRAL_WINDOW" % msfile
        self.tb.open(self.tableName)
        self.parameters = self.tb.colnames()
        self.tb.close()
        self.tb.open(self.tableName)
        self.values = {}
        for i in self.parameters:
            self.values[i] = self.tb.getcell(i, spwId)
        self.tb.close()


def _trimSpwmap(spwMap):
    compare = list(range(len(spwMap)))
    evenPoint = compare[-1]
    i = 0
    for i in compare:
        if compare[i:] == spwMap[i:]:
            evenPoint = i
            break
    return spwMap[:i]


def tsysspwmap(vis, tsystable, trim=True, relax=False, tsysChanTol=0):
    """Generate default spwmap for ALMA Tsys, including TDM->FDM
    associations (ported verbatim in logic from the canonical NRAO
    almahelpers.py; see module docstring)."""
    localTb = _tbtool()
    spwMaps = []
    localTb.open(tsystable)
    measuredTsysSpw = np.unique(localTb.getcol("SPECTRAL_WINDOW_ID"))
    localTb.close()
    localTb.open("%s/SPECTRAL_WINDOW" % tsystable)
    for i in measuredTsysSpw:
        spwMap = _SpwMap(i)
        chanFreqs = localTb.getcell("CHAN_FREQ", int(i))
        chanWidth = abs(chanFreqs[1] - chanFreqs[0])
        spwMap.chanWidth = chanWidth
        spwMap.validFreqRange = [chanFreqs.min() - 0.5 * chanWidth,
                                  chanFreqs.max() + 0.5 * chanWidth]
        spwMaps.append(spwMap)
    localTb.close()
    localTb.open("%s/SPECTRAL_WINDOW" % vis)
    it = localTb.nrows()
    localTb.close()
    for j in spwMaps:
        localTb.open("%s/SPECTRAL_WINDOW" % vis)
        j.bbNo = localTb.getcell("BBC_NO", int(j.calSpwId))
        localTb.close()
        for i in range(it):
            localTb.open("%s/SPECTRAL_WINDOW" % vis)
            chanFreqs = localTb.getcell("CHAN_FREQ", i)
            if len(chanFreqs) > 1:
                chanWidth = localTb.getcell("CHAN_WIDTH", i)[0]
                freqMin = chanFreqs.min() - 0.5 * chanWidth
                freqMax = chanFreqs.max() + 0.5 * chanWidth
            else:
                chanWidth = localTb.getcell("CHAN_WIDTH", i)
                freqMin = chanFreqs - 0.5 * chanWidth
                freqMax = chanFreqs + 0.5 * chanWidth
            localTb.close()
            msSpw = _SpwInfo(vis, i)
            if j.bbNo == msSpw.values['BBC_NO']:
                if (freqMin >= j.validFreqRange[0] - tsysChanTol * j.chanWidth and
                        freqMax <= j.validFreqRange[1] + tsysChanTol * j.chanWidth):
                    j.mapsToSpw.append(i)
    applyCalSpwMap = []
    spwWithoutMatch = []
    localTb.open("%s/SPECTRAL_WINDOW" % vis)
    for i in range(it):
        useSpw = None
        for j in spwMaps:
            if i in j.mapsToSpw:
                if useSpw is not None:
                    if localTb.getcell("BBC_NO", i) == j.bbNo:
                        useSpw = j.calSpwId
                else:
                    useSpw = j.calSpwId
        if useSpw is None:
            useSpw = i
            spwWithoutMatch.append(i)
        applyCalSpwMap.append(int(useSpw))
    localTb.close()
    if trim:
        return _trimSpwmap(applyCalSpwMap)
    else:
        return applyCalSpwMap
