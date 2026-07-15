// 販売チャネルの一元設定(2026-07-14 ソル裁定: 販路切替を設定1つで行えるようにする)
//
// Yahoo→BASE切替時はここの primary_channel を "base" に変えてデプロイするだけ。
// 切替手順の全体は Desktop\fuji_timelapse ではなく docs/channel_switch_runbook.md を参照。
// effective_at は記録用(いつ切り替えたか)。コードでは参照しない。

export const CHANNELS = {
  primary_channel: "yahoo",
  standby_channel: "base",
  effective_at: null,
  destinations: {
    yahoo: "https://store.shopping.yahoo.co.jp/iwatayacom/",
    base: "https://iwatayacom.thebase.in/",
    libe: "https://ichiba.libecity.com/shops/577",
  },
};

export function primaryUrl() {
  return CHANNELS.destinations[CHANNELS.primary_channel];
}
