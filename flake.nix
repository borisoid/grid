{
    inputs = {
        nixPackages.url = "github:NixOS/nixpkgs/nixos-24.05";
        nixPackagesUnstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    };

    outputs = { nixPackages, nixPackagesUnstable, ... }@inputs: let
        system = "x86_64-linux";
        p = nixPackagesUnstable.legacyPackages.${system};
    in {
        devShells.${system}.default = (p.buildFHSEnv {
            name = "py-fhs-env";
            targetPkgs = p: let
                pp = p.python313Packages;
            in [
                (pp.python.withPackages (ppp: [
                    ppp.kiwisolver
                    ppp.pygame

                    ppp.mypy
                    # (ppp.mypy.overrideAttrs rec {
                    #     pname = "mypy";
                    #     version = "1.13.0";
                    #     src = p.fetchFromGitHub {
                    #         owner = "python";
                    #         repo = "mypy";
                    #         rev = "refs/tags/v${version}";
                    #         hash = "sha256-P2Ozmj7/7QBmjlveHLsNdYgUAerg0qOoa8pO0iQc5os=";
                    #     };
                    # })

                    ppp.pytest
                    ppp.typing-extensions
                    ppp.ruff
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
