{
  description = "A very basic flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    #rust-overlay.url = "github:oxalica/rust-overlay";
  };

  outputs = { self, nixpkgs, flake-utils }: #, rust-overlay }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
		  #overlays = [ rust-overlay.overlay ];
          config = {
            allowUnfree = true;
          };
        };
      in
      {
        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [
            #rust-bin.stable.latest.default
			pdfgrep
            (python3.withPackages (ps: with ps; [
              tkinter
              pillow
			  reportlab
			  pypdf2
            ]))
          ];
        };
      }
    );
}
