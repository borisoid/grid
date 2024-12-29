{
    inputs = {
        nixPackagesUnstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    };

    outputs = { nixPackagesUnstable, ... }@inputs: let
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

                    ppp.pytest
                    ppp.ruff

                    ppp.typing-extensions
                    ppp.mypy
                ]))
                p.pyright
            ];

            runScript = "bash";
        }).env;
    };
}
