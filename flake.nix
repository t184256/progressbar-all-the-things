{
  description = "Guesstimate progress of arbitrary process trees with flashy progressbars. ";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  #inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem
      (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          # TODO: replace project-name with a dashed project name
          patt-server = pkgs.python3Packages.buildPythonPackage {
            pname = "progressbar-all-the-things";
            version = "0.0.1";
            src = ./.;
            propagatedBuildInputs = with pkgs.python3Packages; [
              tqdm
            ];
            checkInputs = with pkgs.python3Packages; [
              pytest
              coverage
              flake8
              flake8-import-order
              codespell
            ] ++ [ pkgs.gnumake ];
            checkPhase = "make check";
          };
        in
        {
          packages.patt-server = patt-server;
          defaultPackage = patt-server;
          apps.project-name = flake-utils.lib.mkApp { drv = patt-server; };
          defaultApp = patt-server;
          devShell = import ./shell.nix { inherit pkgs; };
        }
      );
}
