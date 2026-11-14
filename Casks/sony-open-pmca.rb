cask "sony-open-pmca" do
  version "1.3.0"
  sha256 "c2e9b29345879cbc3114ae85c97e8468c021f30bddfc88267a09300700a2a47d"

  url "https://github.com/OpenPMCA/Sony-Open-PMCA/releases/download/v#{version}/Sony-Open-PMCA-#{version}-macos-arm64.zip"
  name "Sony Open PMCA"
  desc "GUI application to manage apps on Sony Alpha cameras"
  homepage "https://github.com/OpenPMCA/Sony-Open-PMCA"

  depends_on arch: :arm64
  depends_on macos: :tahoe

  app "Sony Open PMCA.app"

  zap trash: [
    "~/Library/Saved Application State/org.openpmca.sonyopenpmca.savedState",
  ]
end
