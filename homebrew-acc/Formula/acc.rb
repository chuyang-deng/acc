class Acc < Formula
  include Language::Python::Virtualenv

  desc "Agent Command Center — monitor and manage AI coding agent sessions"
  homepage "https://github.com/chuyang-deng/acc"
  url "https://github.com/chuyang-deng/acc/archive/refs/tags/v0.1.6.tar.gz"
  sha256 "5dbe47db52b9a63ef9d44e85d9055125cf4e92b2c4a3c44775617b0e98cefd00"
  license "AGPL-3.0-only"

  depends_on "python@3.11"
  depends_on "tmux"

  resource "rich" do
    url "https://files.pythonhosted.org/packages/8d/5f/4ae8f6a4a27521c7e63b65a5ee904975e7a9bfa95f403930b2e88a385f9a/rich-13.7.1.tar.gz"
    sha256 "b57e4e1e3260c870295834928b525d8869c9b63484f2b1d3d5771c3059868351"
  end

  resource "markdown-it-py" do
    url "https://files.pythonhosted.org/packages/49/a0/0a8d46153039d9351de63972233b8a13a8c62b694b2a8296317b6da4d84f/markdown-it-py-3.0.0.tar.gz"
    sha256 "e3f60a94fa066dc52ec76661e37c851cb232d92f9886b15cb560aaada2df8feb"
  end

  resource "mdurl" do
    url "https://files.pythonhosted.org/packages/f5/db/8ef372bb46a29bd8fab83a8f4c0840c8855e4e8992d9d10712a20b22a075/mdurl-0.1.2.tar.gz"
    sha256 "bb413d29f5eea38f31dd4754dd7377d44651160b0d5d4f9b1090563b708f1d77"
  end

  resource "pygments" do
    url "https://files.pythonhosted.org/packages/7c/41/5b8f2d65017409403a5518b5358055bfcf5c777d5b169996d929312a0210/Pygments-2.17.2.tar.gz"
    sha256 "da46cec9fd2de5be3a8a77913eb9414872f3e5b3cb090014a7cf6db836df16b8"
  end

  resource "typing_extensions" do
    url "https://files.pythonhosted.org/packages/b7/f4/6a9081a4b9175ee25c78216fc6bfd95267a14e13024c568d40742f9d784a/typing_extensions-4.11.0.tar.gz"
    sha256 "bf49405b22596489a243d63968270275822f357564d26258410229334d7d6560"
  end

  resource "textual" do
    url "https://files.pythonhosted.org/packages/9f/38/7d169a765993efde5095c70a668bf4f5831bb7ac099e932f2783e9b71abf/textual-7.5.0.tar.gz"
    sha256 "c730cba1e3d704e8f1ca915b6a3af01451e3bca380114baacf6abf87e9dac8b6"
  end

  resource "anyio" do
    url "https://files.pythonhosted.org/packages/88/2c/8334465355a2977e1694f42eb2a798ed2add07b789128f73f8a02d4b9714/anyio-4.3.0.tar.gz"
    sha256 "b2c9339e102241cf0728c30fb3950b7301c51db3fcc7517865c697816823469e"
  end

  resource "idna" do
    url "https://files.pythonhosted.org/packages/1d/a3/9ecdc42436ee68007a488eb7ad9e583c4a45a343b664d47f925b42e7421c/idna-3.7.tar.gz"
    sha256 "028ff3aadf05502360a558567495ae402434b3e8958434cd66c9ff506f36616d"
  end

  resource "sniffio" do
    url "https://files.pythonhosted.org/packages/ee/7e/1557085c2759e35928f664560f78bd3327d7dd271b14ad60676b66ac098c/sniffio-1.3.1.tar.gz"
    sha256 "f434771033230a84dfc85be84497a7e3240ea0d36480df96898436cd97380cf0"
  end

  resource "distro" do
    url "https://files.pythonhosted.org/packages/cc/83/82ba52424b94f57c672b11568e6f3eb24cc353f47e25d259586146c672a9/distro-1.9.0.tar.gz"
    sha256 "2fa77c6fd8940f116ee1d6b94a2f9dc4f8cd83c31623d3239656cf0d2d3e913e"
  end

  resource "h11" do
    url "https://files.pythonhosted.org/packages/95/04/ff642e65ad6b90db43e668d70ffb6736436c7ce41fcc549f4e9472234162/h11-0.14.0.tar.gz"
    sha256 "8f19fbbe99e724075909add0e9d1f1d0066f543e1dcb33ee92a72f05b1975310"
  end

  resource "httpcore" do
    url "https://files.pythonhosted.org/packages/78/d4/e5d7e4f2174f8a4d638d42d316a3df789456e43034c5685799b66b7d1843/httpcore-1.0.5.tar.gz"
    sha256 "34a38e2f9291467ee3b44e89dd52615370e152954ba21721378a87b2960f7a61"
  end

  resource "httpx" do
    url "https://files.pythonhosted.org/packages/41/7b/ddacf6dcebb42466abd03f36878214296fbdb465016350651085b96efcb2/httpx-0.27.0.tar.gz"
    sha256 "fbb71db199a07d642db86cf97978eb3cc7d8f368f5c889de3403d52d3d943c2c"
  end

  resource "jiter" do
    url "https://files.pythonhosted.org/packages/8d/62/d665a363a02a4669f6885df422964b4136e7a637a544b6c319eb382c7f66/jiter-0.4.0.tar.gz"
    sha256 "22998f8b1c4b78fa8e2bf91c8cf7543d34a413009599589a19430c5123d90595"
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
      acc requires tmux to be running with coding agent sessions.
      Start agents in tmux windows, then run `acc` to monitor them.

      Supported agents: Claude, OpenCode, Codex, Aider, Gemini/Antigravity
      Optional: Set ANTHROPIC_API_KEY for LLM-powered session summaries.

      Config: ~/.acc/config.yaml
    EOS
  end

  test do
    assert_match "acc", shell_output("#{bin}/acc --help 2>&1", 2)
  end
end
