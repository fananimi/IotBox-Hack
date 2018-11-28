 # -*- coding: utf-8 -*-
import platform

RELEASE_LEVELS = [ALPHA, BETA, RELEASE_CANDIDATE, FINAL] = ['alpha', 'beta', 'candidate', 'final']
RELEASE_LEVELS_DISPLAY = {ALPHA: ALPHA,
                          BETA: BETA,
                          RELEASE_CANDIDATE: 'rc',
                          FINAL: ''}

# version_info format: (MAJOR, MINOR, MICRO, OS, ARCH)
os = 'Mac' if platform.system().lower() == 'darwin' else platform.system()
version_info = (1, 0, 0, ALPHA, os)
version = '.'.join(str(s) for s in version_info[:2]) + RELEASE_LEVELS_DISPLAY[version_info[3]] + " " + "(" + str(version_info[4]) + ")"
series = serie = major_version = '.'.join(str(s) for s in version_info[:2])

