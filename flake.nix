{
    inputs = {
        nixPackages.url = "github:NixOS/nixpkgs/nixos-24.05";
    };

    outputs = { nixPackages, ... }@inputs:
    let
        system = "x86_64-linux";

        p = nixPackages.legacyPackages.${system};
        pp = p.python312Packages;

        inherit (nixPackages) lib;
    in {
        devShells.${system}.default = (p.buildFHSUserEnv {
            name = "py-fhs-env";
            targetPkgs = p: [
                (pp.python.withPackages (ppp: [
                    ppp.kiwisolver
                    ppp.pygame

                    ppp.pytest
                    ppp.typing-extensions
                    ppp.mypy
                    ppp.black
                    ppp.isort
                ]))
                p.pyright

                p.stdenv
                p.stdenv.cc.cc.lib
                p.stdenv.cc.cc
                p.gcc

                p.taglib
                p.openssl
                p.git
                p.libxml2
                p.libxslt
                p.libzip
                p.zlib
            ];

            runScript = "bash";
        }).env;
    };
}
