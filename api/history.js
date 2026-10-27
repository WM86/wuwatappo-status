const RAW = "https://raw.githubusercontent.com/WM86/wuwatappo-status/master/data/history.json";

// 把仓库里的探测结果实时转出来：不缓存，每次回源头取一遍。
// （直接让 Vercel 用 rewrite 转会被边缘缓存住，实测滞后二十分钟以上，所以走函数。）
module.exports = async (req, res) => {
  try {
    const upstream = await fetch(RAW + "?cb=" + Date.now(), {
      cache: "no-store",
      headers: { "cache-control": "no-cache", pragma: "no-cache" },
    });
    if (!upstream.ok) throw new Error("upstream " + upstream.status);
    const text = await upstream.text();
    res.setHeader("Content-Type", "application/json; charset=utf-8");
    res.setHeader("Cache-Control", "no-store, max-age=0, must-revalidate");
    res.status(200).send(text);
  } catch (err) {
    res.setHeader("Cache-Control", "no-store");
    res.status(502).json({ error: String((err && err.message) || err) });
  }
};
