# Maintainer: Owlopia & infinitydecoder <contact@owlopia.dev>
pkgname=dorkmaster
pkgver=0.1.0
pkgrel=1
pkgdesc="Automated Google Dorking and OSINT Reconnaissance Tool (Kali Linux, Debian, Arch, BlackArch)"
arch=('any')
url="https://github.com/owlopia/dorkmaster"
license=('MIT')
depends=(
    'python'
    'python-beautifulsoup4'
    'python-tabulate'
)
makedepends=('python-setuptools' 'python-build' 'python-wheel')

package() {
    mkdir -p "${pkgdir}/usr/bin"
    mkdir -p "${pkgdir}/usr/lib/python3/dist-packages/dorkmaster"
    mkdir -p "${pkgdir}/usr/share/dorkmaster"
    mkdir -p "${pkgdir}/usr/share/applications"
    mkdir -p "${pkgdir}/usr/share/icons/hicolor/128x128/apps"
    mkdir -p "${pkgdir}/usr/share/licenses/dorkmaster"

    cp -r "${srcdir}/dorkmaster/"* "${pkgdir}/usr/lib/python3/dist-packages/dorkmaster/" 2>/dev/null || cp -r dorkmaster/* "${pkgdir}/usr/lib/python3/dist-packages/dorkmaster/"

    if [ -f "data/dorks.json" ]; then
        cp data/dorks.json "${pkgdir}/usr/share/dorkmaster/dorks.json"
    elif [ -f "dorkmaster/data/dorks.json" ]; then
        cp dorkmaster/data/dorks.json "${pkgdir}/usr/share/dorkmaster/dorks.json"
    fi

    printf '#!/usr/bin/env python3\nimport sys\nfrom dorkmaster.cli import main\n\nif __name__ == "__main__":\n    sys.exit(main())\n' > "${pkgdir}/usr/bin/dorkmaster"
    chmod 755 "${pkgdir}/usr/bin/dorkmaster"

    if [ -f "dorkmaster.desktop" ]; then
        cp dorkmaster.desktop "${pkgdir}/usr/share/applications/"
    fi
    if [ -f "assets/DorkMaster.png" ]; then
        cp assets/DorkMaster.png "${pkgdir}/usr/share/icons/hicolor/128x128/apps/dorkmaster.png"
        cp assets/DorkMaster.png "${pkgdir}/usr/share/icons/hicolor/128x128/apps/DorkMaster.png"
    elif [ -f "assets/dorkmaster.png" ]; then
        cp assets/dorkmaster.png "${pkgdir}/usr/share/icons/hicolor/128x128/apps/dorkmaster.png"
    fi
    if [ -f "LICENSE" ]; then
        cp LICENSE "${pkgdir}/usr/share/licenses/dorkmaster/LICENSE"
    fi
}
