{
  description = "Environment for CITA expense report generator";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }: #, rust-overlay }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config = {
            allowUnfree = true;
          };
        };
      in
      {
        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [
			pdfgrep
			cargo
			rustc
            (python311.withPackages (ps: with ps; [
              tkinter
              pillow
			  reportlab
			  pypdf2
			  pdf2image
            ]))
          ];
        };
      }
    );
}
