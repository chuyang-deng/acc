class Ccc < Formula
  include Language::Python::Virtualenv

  desc "TUI to monitor coding agent sessions (Claude, OpenCode, Codex, Aider, Gemini) in tmux"
  homepage "https://github.com/cyy/ccc"
  url "file://#{Dir.home}/repos/ccc/dist/claude_command_center-0.1.2.tar.gz"
  sha256 "3e018efba451bf3ad05037fd9eafa4da81cc60d49db6830cf8eedfa65d5ce9ea"
  license "MIT"

  depends_on "python@3.13"
  depends_on "tmux"

  resource "textual" do
    url "https://files.pythonhosted.org/packages/9f/38/7d169a765993efde5095c70a668bf4f5831bb7ac099e932f2783e9b71abf/textual-7.5.0.tar.gz"
    sha256 "c730cba1e3d704e8f1ca915b6a3af01451e3bca380114baacf6abf87e9dac8b6"
  end

  resource "anthropic" do
    url "https://files.pythonhosted.org/packages/15/b1/91aea3f8fd180d01d133d931a167a78a3737b3fd39ccef2ae8d6619c24fd/anthropic-0.79.0.tar.gz"
    sha256 "8707aafb3b1176ed6c13e2b1c9fb3efddce90d17aee5d8b83a86c70dcdcca871"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/05/8e/961c0007c59b8dd7729d542c61a4d537767a59645b82a0b521206e1e25c2/pyyaml-6.0.3.tar.gz"
    sha256 "d76623373421df22fb4cf8817020cbb7ef15c725b9d5e45f17e189bfc384190f"
  end

  resource "psutil" do
    url "https://files.pythonhosted.org/packages/aa/c6/d1ddf4abb55e93cebc4f2ed8b5d6dbad109ecb8d63748dd2b20ab5e57ebe/psutil-7.2.2.tar.gz"
    sha256 "0746f5f8d406af344fd547f1c8daa5f5c33dbc293bb8d6a16d80b4bb88f59372"
  end

  def install
    virtualenv_install_with_resources
  end

  def caveats
    <<~EOS
      ccc requires tmux to be running with coding agent sessions.
      Start agents in tmux windows, then run `ccc` to monitor them.

      Supported agents: Claude, OpenCode, Codex, Aider, Gemini/Antigravity
      Optional: Set ANTHROPIC_API_KEY for LLM-powered session summaries.

      Config: ~/.config/ccc/config.yaml
    EOS
  end

  test do
    assert_match "ccc", shell_output("#{bin}/ccc --help 2>&1", 2)
  end
end
