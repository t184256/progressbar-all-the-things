{ pkgs ? import <nixpkgs> { } }:
pkgs.mkShell {
  buildInputs = with pkgs; [
    (python3.withPackages (ps: with ps; [
      tqdm
    ]))
  ];
  nativeBuildInputs = with pkgs.python3Packages; [
    flake8
    flake8-import-order
    codespell
  ] ++ [ pkgs.gnumake ];
}
