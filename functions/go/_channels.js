// 販売チャネルの一元設定(2026-07-14 ソル裁定: 販路切替を設定1つで行えるようにする)
//
// Yahoo→BASE切替時はここの primary_channel を "base" に変えてデプロイするだけ。
// 切替手順の全体は Desktop\fuji_timelapse ではなく docs/channel_switch_runbook.md を参照。
// effective_at は記録用(いつ切り替えたか)。コードでは参照しない。

// 2026-08-08: Yahoo!ショッピング店は2026-09-30で解約するため destinations から外した。
// これで /go/buy/yahoo は転送先が見つからず、安全に予約LP(/reserve/)へ落ちる。
// 過去に配ったリンク(YouTube動画5本など)が9/30以降に行き止まりにならないための措置。
// 解約前に前倒しで切ったのは、店じまい中に新規注文が入るのを防ぐため。
export const CHANNELS = {
  primary_channel: "base",
  standby_channel: "libe",
  effective_at: "2026-08-08T00:00:00+09:00",
  destinations: {
    base: "https://iwatayacom.thebase.in/",
    libe: "https://ichiba.libecity.com/shops/577",
  },
};

export function primaryUrl() {
  return CHANNELS.destinations[CHANNELS.primary_channel];
}
