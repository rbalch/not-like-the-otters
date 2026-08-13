{
  # Client-side shell only. The dev container on the server builds and tests this
  # project headlessly; this flake exists for the one thing it cannot do — open the
  # real Tauri window on a machine with a display.
  #
  #   rsync -a --delete --exclude target --exclude node_modules --exclude .venv \
  #     server:/path/to/not-like-the-otters/ ./not-like-the-otters/
  #   cd not-like-the-otters && nix develop -c cargo tauri dev
  #
  # Note: flakes only see git-tracked files, so `git add` a new file before it will
  # resolve here.

  description = "not-like-the-otters — Tauri dev shell for a machine with a display";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};

          # Shared by the compile step and the run step. Kept in one list so the
          # LD_LIBRARY_PATH below cannot drift from what pkg-config found.
          tauriLibs = with pkgs; [
            webkitgtk_4_1
            gtk3
            libsoup_3
            librsvg
            libayatana-appindicator
            openssl
            glib
            cairo
            pango
            gdk-pixbuf
            atk
          ];
        in
        {
          default = pkgs.mkShell {
            nativeBuildInputs = with pkgs; [
              pkg-config
              wrapGAppsHook3
            ];

            buildInputs =
              tauriLibs
              ++ (with pkgs; [
                # Matches the container: rust stable, node 24, the Tauri CLI.
                rustc
                cargo
                rustfmt
                clippy
                rust-analyzer
                nodejs_24
                cargo-tauri

                # Without glib-networking, webkit has no TLS backend and every https
                # request inside the webview fails with a useless error.
                glib-networking

                # GTK apps abort at startup if their gsettings schemas are missing.
                gsettings-desktop-schemas
              ]);

            shellHook = ''
              export RUST_SRC_PATH="${pkgs.rustPlatform.rustLibSrc}"

              # webkitgtk picks broken paths on NixOS unless it is told where TLS
              # modules live.
              export GIO_MODULE_DIR="${pkgs.glib-networking}/lib/gio/modules/"

              export XDG_DATA_DIRS="${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}:${pkgs.gtk3}/share/gsettings-schemas/${pkgs.gtk3.name}:$XDG_DATA_DIRS"

              export LD_LIBRARY_PATH="${nixpkgs.lib.makeLibraryPath tauriLibs}:$LD_LIBRARY_PATH"

              # Two long-standing webkitgtk failure modes on Linux desktops: a blank
              # white window under compositing, and a crash in the dmabuf renderer on
              # some drivers. Both are cheap to disable and only affect this dev shell.
              export WEBKIT_DISABLE_COMPOSITING_MODE=1
              export WEBKIT_DISABLE_DMABUF_RENDERER=1

              echo "tauri dev shell — run: cargo tauri dev"
            '';
          };
        }
      );
    };
}
