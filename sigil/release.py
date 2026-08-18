

RELEASE_LEVELS = [ALPHA, BETA, RELEASE_CANDIDATE, FINAL] = ['alpha', 'beta', 'candidate', 'final']
RELEASE_LEVELS_DISPLAY = {ALPHA: 'a',
                          BETA: 'b',
                          RELEASE_CANDIDATE: 'rc',
                          FINAL: ''}

# version_info format: (MAJOR, MINOR, MICRO, RELEASE_LEVEL, SERIAL)
# inspired by Python's own sys.version_info, in order to be
# properly comparable using normal operators, for example:
#  (6,1,0,'beta',0) < (6,1,0,'candidate',1) < (6,1,0,'candidate',2)
#  (6,1,0,'candidate',2) < (6,1,0,'final',0) < (6,1,2,'final',0)
# NOTE: during release, the MAJOR version can become an arbitrary string ('saas~xx')
version_info = (2, 2, 2, FINAL, 0, '+e')
series = serie = major_version = '.'.join(str(s) for s in version_info[:2])
version = series + RELEASE_LEVELS_DISPLAY[version_info[3]] + str(version_info[4] or '') + version_info[5]

product_name = 'Sigil'
description = 'Sigil Server'
long_desc = '''Sigil is a modular server runtime designed for building
and operating internal systems and services. It provides a structured
core for configuration, data management, service orchestration,
and extensible application layers.
'''
classifiers = """Development Status :: 1 - Planning
License :: OSI Approved :: GNU Lesser General Public License v3

Programming Language :: Python
"""
url = 'https://www.iantirta.com'
author = 'Iantirta Labs'
author_email = 'info@iantirta.com'
license = 'LGPL-3'

nt_service_name = "sigil-server-" + series.replace('~','-')

MIN_PY_VERSION = (3, 10)
MAX_PY_VERSION = (3, 13)
MIN_PG_VERSION = 13
