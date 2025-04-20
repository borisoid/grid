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
                pPy = p.python313Packages;
            in [
                (pPy.python.withPackages (p: [
                    p.kiwisolver
                    p.pygame

                    p.pytest
                    p.ruff

                    p.typing-extensions
                    p.mypy
                ]))
                p.pyright
            ];

            # runScript = "bash";
        }).env;
    };
}
