{pkgs}: {
  deps = [
    pkgs.pango
    pkgs.harfbuzz
    pkgs.glib
    pkgs.ghostscript
    pkgs.fontconfig
    pkgs.vim-full
    pkgs.rustc
    pkgs.pkg-config
    pkgs.openssl
    pkgs.libxcrypt
    pkgs.libiconv
    pkgs.cargo
  ];
}
