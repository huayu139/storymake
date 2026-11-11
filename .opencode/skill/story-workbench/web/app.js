/* Story Lab 只读看板前端 —— 零依赖原生 JS */

const state = { slug: null, projects: [], view: "overview" };
const $ = (sel) => document.querySelector(sel);
const app = $("#app");

/* ---------------------------------------------------------------- 基础 */
function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function splitRow(line) {
  return line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((s) => s.trim());
}

function md(src) {
  if (!src || !String(src).trim()) return '<p class="dim">（暂无内容）</p>';
  const lines = String(src).replace(/\r\n/g, "\n").split("\n");
  const inline = (s) => esc(s)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*\n]+)\*/g, "<em>$1</em>");
  const out = [];
  let i = 0, inCode = false, code = [];
  while (i < lines.length) {
    const line = lines[i];
    if (/^```/.test(line)) {
      if (inCode) { out.push("<pre><code>" + esc(code.join("\n")) + "</code></pre>"); code = []; inCode = false; }
      else inCode = true;
      i++; continue;
    }
    if (inCode) { code.push(line); i++; continue; }
    if (!line.trim()) { i++; continue; }
    let m;
    if ((m = line.match(/^(#{1,6})\s+(.*)$/))) {
      const n = m[1].length;
      out.push(`<h${n}>${inline(m[2])}</h${n}>`); i++; continue;
    }
    if (/^\s*(---+|___+|\*\*\*+)\s*$/.test(line)) { out.push("<hr>"); i++; continue; }
    if (/^\s*>\s?/.test(line)) {
      const buf = [];
      while (i < lines.length && /^\s*>\s?/.test(lines[i])) { buf.push(lines[i].replace(/^\s*>\s?/, "")); i++; }
      out.push("<blockquote>" + buf.map(inline).join("<br>") + "</blockquote>"); continue;
    }
    if (line.includes("|") && i + 1 < lines.length && /^\s*\|?[\s:|-]+\|[\s:|-]*$/.test(lines[i + 1])) {
      const headers = splitRow(line);
      i += 2;
      const rows = [];
      while (i < lines.length && lines[i].trim() && lines[i].includes("|")) { rows.push(splitRow(lines[i])); i++; }
      out.push("<table><thead><tr>" + headers.map((h) => `<th>${inline(h)}</th>`).join("") +
        "</tr></thead><tbody>" + rows.map((r) => "<tr>" + r.map((c) => `<td>${inline(c)}</td>`).join("") + "</tr>").join("") +
        "</tbody></table>");
      continue;
    }
    if ((m = line.match(/^\s*[-*+]\s+(.*)$/))) {
      const items = [];
      while (i < lines.length && (m = lines[i].match(/^\s*[-*+]\s+(.*)$/))) { items.push(m[1]); i++; }
      out.push("<ul>" + items.map((x) => `<li>${inline(x)}</li>`).join("") + "</ul>"); continue;
    }
    if ((m = line.match(/^\s*\d+[.)]\s+(.*)$/))) {
      const items = [];
      while (i < lines.length && (m = lines[i].match(/^\s*\d+[.)]\s+(.*)$/))) { items.push(m[1]); i++; }
      out.push("<ol>" + items.map((x) => `<li>${inline(x)}</li>`).join("") + "</ol>"); continue;
    }
    const para = [];
    while (i < lines.length && lines[i].trim() &&
      !/^(#{1,6})\s|^\s*[-*+]\s|^\s*\d+[.)]\s|^\s*>\s?/.test(lines[i])) {
      para.push(lines[i]); i++;
    }
    out.push("<p>" + para.map(inline).join("<br>") + "</p>");
  }
  if (inCode && code.length) out.push("<pre><code>" + esc(code.join("\n")) + "</code></pre>");
  return out.join("\n");
}

function statusClass(raw) {
  if (raw === "通过") return "ok";
  if (raw === "待修" || raw === "异常") return "bad";
  if (raw === "卡片" || raw === "待评") return "mid";
  return "idle";
}

function badge(text, cls = "") {
  return `<span class="badge ${cls}">${esc(text)}</span>`;
}

function fmt(value, fallback = "—") {
  return value === null || value === undefined || value === "" ? fallback : value;
}

function toast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.remove("show"), 2200);
}

async function api(path) {
  const res = await fetch(path, { cache: "no-store" });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

/* ---------------------------------------------------------------- 路由 */
function parseHash() {
  const h = location.hash.replace(/^#\/?/, "");
  const [view, arg] = h.split("/");
  return { view: view || "overview", arg: arg ? Number(arg) : null };
}

function setActiveTab(view) {
  const tabView = view === "episode" ? "episodes" : view;
  document.querySelectorAll("#tabs a").forEach((a) => {
    a.classList.toggle("active", a.dataset.view === tabView);
  });
}

async function route() {
  const { view, arg } = parseHash();
  state.view = view;
  setActiveTab(view);
  if (!state.slug) return;
  app.innerHTML = '<div class="loading">正在读取磁盘…</div>';
  try {
    const base = `/api/project/${encodeURIComponent(state.slug)}`;
    if (view === "episode") {
      app.innerHTML = renderEpisode(await api(`${base}/episode/${arg}`));
    } else if (view === "episodes") {
      app.innerHTML = renderEpisodes(await api(`${base}/episodes`));
    } else if (view === "bible") {
      app.innerHTML = renderBible(await api(`${base}/bible`));
    } else if (view === "structure") {
      app.innerHTML = renderStructure(await api(`${base}/structure`));
    } else if (view === "continuity") {
      app.innerHTML = renderContinuity(await api(`${base}/continuity`));
    } else if (view === "decisions") {
      app.innerHTML = renderDecisions(await api(`${base}/decisions`));
    } else {
      app.innerHTML = renderOverview(await api(`${base}/overview`));
    }
    window.scrollTo({ top: 0 });
  } catch (err) {
    app.innerHTML = `<div class="panel"><h2>读取失败</h2><p class="muted">${esc(err.message)}</p>
      <p class="small dim">请确认 webview.py 正在运行，且项目文件存在。</p></div>`;
  }
}

/* ---------------------------------------------------------------- 总览 */
function renderOverview(d) {
  const p = d.progress;
  const story = d.story;
  const q = d.quality;
  const project = d.project || {};
  const movements = d.movements.map((m) => `
    <div class="movement">
      <div class="top">
        <span>乐章 ${m.id} · ${esc(m.name)} <span class="dim small">e${String(m.start).padStart(2, "0")}–e${String(m.end).padStart(2, "0")}</span></span>
        <span class="mono">${m.done}/${m.total}</span>
      </div>
      <div class="goal">${esc(m.goal)}</div>
      <div class="bar"><i style="width:${m.percent}%"></i></div>
    </div>`).join("");

  const next = d.next.map((e) => `
    <div class="scene">
      <div class="spread">
        <a class="sid" href="#/episode/${e.ep}">e${String(e.ep).padStart(2, "0")} · ${esc(e.status)}</a>
        ${e.cliffhanger ? badge(e.cliffhanger, "accent") : ""}
      </div>
      <div class="obj">${esc(e.hook || "暂无钩子")}</div>
      <div class="small dim">${esc(e.value_before || "—")} → ${esc(e.value_after || "—")}${e.pinned ? " · 钉死集" : ""}</div>
    </div>`).join("") || '<div class="empty-box">暂无后续集</div>';

  const knows = (story.protagonist.knows || []).map((x) => `<li>${esc(x)}</li>`).join("") || "<li class='dim'>—</li>";
  const believes = (story.protagonist.believes || []).map((x) => `<li>${esc(x)}</li>`).join("") || "<li class='dim'>—</li>";
  const suspects = (story.protagonist.suspects || []).map((x) => `<li>${esc(x)}</li>`).join("") || "<li class='dim'>—</li>";

  const threads = (d.threads || []).map((t) => {
    const cls = /已回收/.test(t.state) ? "ok" : /逾期/.test(t.state) ? "bad" : /推进|埋设/.test(t.state) ? "warn" : "idle";
    return `<tr>
      <td class="mono">${esc(t.id)}</td>
      <td>${esc(t.desc)}</td>
      <td class="mono">e${String(t.plant).padStart(2, "0")}</td>
      <td class="mono">e${String(t.payoff).padStart(2, "0")}</td>
      <td>${badge(t.state, cls)}</td>
    </tr>`;
  }).join("") || `<tr><td colspan="5" class="dim">暂无伏笔</td></tr>`;

  const recent = (d.recent || []).map((e) => `<tr>
      <td><a href="#/episode/${e.ep}" class="mono">e${String(e.ep).padStart(2, "0")}</a></td>
      <td>${badge(e.status, statusClass(e.raw_status))}</td>
      <td class="mono">${fmt(e.review_total)}/${fmt(e.review_threshold)}</td>
      <td>${esc(e.review_verdict || "—")}</td>
      <td class="mono">${e.script_seconds ? e.script_seconds + "s" : "—"}</td>
    </tr>`).join("") || `<tr><td colspan="5" class="dim">暂无已通过集</td></tr>`;

  const issues = (q.data_issues || []).map((x) => `<li>${esc(x)}</li>`).join("") || "<li class='dim'>未发现数据问题</li>";

  return `
  <section class="hero">
    <div class="kicker">Story Lab · 只读看板</div>
    <h1>《${esc(project.title || state.slug)}》</h1>
    <div class="logline">${esc(d.logline || "")}</div>
    <div class="meta">
      <span>题材 <b>${esc(project.genre || "—")}</b></span>
      <span>平台 <b>${esc(project.platform || "—")}</b></span>
      <span>规模 <b>${fmt(project.episodes)} 集 × ${fmt(project.seconds_per_episode)} 秒</b></span>
      <span>受众 <b>${esc(project.audience || "—")}</b></span>
      <span>决策 <b>${fmt(story.decisions)} 条</b></span>
    </div>
    <div class="progress-wrap">
      <div class="progress-top"><span>全季进度</span><span class="mono">${p.passed} / ${p.total} · ${p.percent}%</span></div>
      <div class="bar"><i style="width:${p.percent}%"></i></div>
    </div>
  </section>

  <div class="grid cols-4" style="margin-bottom:16px">
    <div class="panel stat"><div class="label">已通过</div><div class="value ok">${p.passed}</div><div class="hint">共 ${p.total} 集</div></div>
    <div class="panel stat"><div class="label">已写剧本</div><div class="value">${p.written}</div><div class="hint">含待评/待修</div></div>
    <div class="panel stat"><div class="label">当前集</div><div class="value accent">e${String(p.current_ep).padStart(2, "0")}</div><div class="hint">下一步</div></div>
    <div class="panel stat"><div class="label">质量</div><div class="value ${q.blockers ? "bad" : "ok"}">${q.blockers} / ${q.warnings}</div><div class="hint">未解决 blocker / warning</div></div>
  </div>

  <div class="grid cols-2">
    <section class="panel">
      <h2>五乐章进度 <span class="small dim">${p.movement_passed}/${p.total}</span></h2>
      ${movements || '<div class="empty-box">暂无乐章</div>'}
    </section>
    <div class="stack">
      <section class="panel">
        <h2>接下来 3 集</h2>
        ${next}
      </section>
      <section class="panel">
        <h2>故事现在到哪</h2>
        <div class="hook">
          <div class="q">${esc(story.question || "暂无")}</div>
          <div class="meta">e${String(story.last_ep).padStart(2, "0")} 末价值：${esc(story.last_value || "—")} · 未回收伏笔：${esc((story.open_threads || []).join(", ") || "—")}</div>
        </div>
        <h4 style="color:var(--muted);font-size:12px;margin:16px 0 6px">${esc(story.protagonist.name || "主角")} 当前状态</h4>
        <div class="grid cols-3" style="gap:10px">
          <div><div class="small dim">知道</div><ul class="small">${knows}</ul></div>
          <div><div class="small dim">判断</div><ul class="small">${believes}</ul></div>
          <div><div class="small dim">起疑</div><ul class="small">${suspects}</ul></div>
        </div>
      </section>
    </div>
  </div>

  <div class="grid cols-2" style="margin-top:16px">
    <section class="panel">
      <h2>伏笔账本 <span class="small dim">${(d.threads || []).length} 条</span></h2>
      <table><thead><tr><th>ID</th><th>伏笔</th><th>埋设</th><th>回收</th><th>状态</th></tr></thead><tbody>${threads}</tbody></table>
    </section>
    <div class="stack">
      <section class="panel">
        <h2>最近完成</h2>
        <table><thead><tr><th>集</th><th>状态</th><th>评审</th><th>结论</th><th>时长</th></tr></thead><tbody>${recent}</tbody></table>
      </section>
      <section class="panel">
        <h2>数据健康 <span class="small dim">${(q.data_issues || []).length} 条</span></h2>
        <ul class="small">${issues}</ul>
      </section>
    </div>
  </div>

  <p class="small dim" style="margin-top:18px">生成时间：${esc(d.generated)} · 事实源：project.yaml / bible / structure / episodes</p>`;
}

/* ---------------------------------------------------------------- 分集 */
function renderEpisodes(d) {
  const eps = d.episodes || [];
  const cells = eps.map((e) => {
    const cls = statusClass(e.raw_status);
    const title = [e.hook, e.cliffhanger, e.review_total != null ? `评审 ${e.review_total}/${e.review_threshold}` : ""]
      .filter(Boolean).join(" · ");
    return `<a class="ep-cell ${cls} ${e.pinned ? "pinned" : ""}" href="#/episode/${e.ep}" title="${esc(title)}">
      <span class="n">e${String(e.ep).padStart(2, "0")}${e.pinned ? " ★" : ""}</span>
      <span class="s">${esc(e.status)}</span>
    </a>`;
  }).join("");

  return `
  <div class="page-head">
    <div>
      <h1>分集进度</h1>
      <div class="sub">${eps.length} 集 · 点击任意一集查看场景卡、剧本、状态与评审</div>
    </div>
    <div class="legend">
      <span><i style="background:var(--ok)"></i>已通过</span>
      <span><i style="background:var(--warn)"></i>制作中</span>
      <span><i style="background:var(--bad)"></i>待修/异常</span>
      <span><i style="background:var(--idle)"></i>未开始</span>
      <span>★ 钉死集</span>
    </div>
  </div>
  <section class="panel">
    <div class="ep-grid">${cells}</div>
  </section>`;
}

/* ---------------------------------------------------------------- 单集 */
function renderEpisode(d) {
  const s = d.summary || {};
  const proj = d.project || {};
  const hook = d.hook || {};
  const names = d.character_names || {};
  const nm = (id) => names[id] || id;

  const cards = (d.cards || []).map((c) => {
    const cast = (c.cast || []).map((x) => `<span class="badge">${esc(nm(x))}</span>`).join(" ");
    const must = (c.must_happen || []).map((x) => `<li>${esc(x)}</li>`).join("");
    const mustNot = (c.must_not_happen || []).map((x) => `<li>${esc(x)}</li>`).join("");
    const info = c.information_delta && typeof c.information_delta === "object"
      ? Object.entries(c.information_delta).map(([k, v]) => `<li><b>${esc(k === "audience" ? "观众" : k === "hidden" ? "隐藏" : nm(k))}</b>：${esc(v)}</li>`).join("")
      : "";
    return `<div class="scene">
      <div class="spread">
        <div>
          <div class="sid">${esc(c.scene_id || "")}</div>
          <div class="loc">${esc(c.location || "")}${c.time ? ` · ${esc(c.time)}` : ""}</div>
        </div>
        <span class="badge">${fmt(c.estimated_seconds)}s</span>
      </div>
      <div class="row" style="margin-top:6px">${cast}</div>
      <div class="obj"><b>目标</b>：${esc(c.objective || "—")}<br><b>阻碍</b>：${esc(c.obstacle || "—")}</div>
      <div class="value-shift">价值 <b>${esc(c.value_before || "—")}</b> → <b>${esc(c.value_after || "—")}</b></div>
      ${must ? `<h4 style="color:var(--muted);font-size:12px;margin:12px 0 2px">必须发生</h4><ul class="small">${must}</ul>` : ""}
      ${mustNot ? `<h4 style="color:var(--muted);font-size:12px;margin:12px 0 2px">禁止发生</h4><ul class="small">${mustNot}</ul>` : ""}
      ${info ? `<h4 style="color:var(--muted);font-size:12px;margin:12px 0 2px">信息变化</h4><ul class="small">${info}</ul>` : ""}
      ${c.turn ? `<div class="small muted" style="margin-top:10px"><b>转折</b>：${esc(c.turn)}</div>` : ""}
    </div>`;
  }).join("") || '<div class="empty-box">本集还没有场景卡</div>';

  const state = d.state || {};
  const chars = state.characters || {};
  const charCards = Object.entries(chars).map(([id, c]) => {
    const list = (arr) => (arr || []).map((x) => `<li>${esc(x)}</li>`).join("") || "<li class='dim'>—</li>";
    return `<div class="char-card">
      <h3><span>${esc(nm(id))}</span><span class="id">${esc(id)}</span></h3>
      <div class="small dim">位置：${esc(c.location || "—")} · 持有：${esc((c.holds || []).join("、") || "—")}</div>
      <h4>知道</h4><ul>${list(c.knows)}</ul>
      <h4>判断</h4><ul>${list(c.believes)}</ul>
      <h4>起疑</h4><ul>${list(c.suspects)}</ul>
      ${(c.must_not_know || []).length ? `<h4>不能知道</h4><ul>${list(c.must_not_know)}</ul>` : ""}
    </div>`;
  }).join("") || '<div class="empty-box">本集还没有 state.yaml</div>';

  const props = Object.entries(state.props || {}).map(([k, v]) => `<tr>
      <td class="mono">${esc(k)}</td><td>${esc(v.status || "—")}</td><td>${esc(v.holder ? nm(v.holder) : "—")}</td>
    </tr>`).join("");

  const review = d.review || {};
  const scores = Object.entries(review.scores || {}).map(([k, v]) => `
    <details class="review-block">
      <summary><span>${esc(k)}</span><span class="score"><span class="n">${fmt(v.score)}</span>/5</span></summary>
      <div class="small muted">${md(v.evidence || "")}</div>
    </details>`).join("");
  const issues = (review.issues || []).map((i) => {
    const level = (i.severity || "warning").toUpperCase();
    return `<div class="issue ${level === "BLOCKER" ? "BLOCKER" : "WARN"}">
      <span class="rule">${esc(i.code || i.rule || "")}</span>
      <div>${esc(i.message || i.msg || JSON.stringify(i))}</div>
    </div>`;
  }).join("");

  return `
  <div class="page-head">
    <div>
      <div class="small"><a href="#/episodes">← 返回分集</a></div>
      <div class="page-title" style="margin-top:4px">
        <h1>e${String(s.ep).padStart(2, "0")} · 第 ${s.ep} 集</h1>
        ${badge(s.status, statusClass(s.raw_status))}
        ${s.review_total != null ? badge(`评审 ${s.review_total}/${s.review_threshold}`, s.review_verdict === "approved" ? "ok" : "warn") : ""}
        ${s.script_seconds ? badge(`${s.script_seconds}s`, "accent") : ""}
        ${s.pinned ? badge("钉死集", "accent") : ""}
      </div>
      <div class="sub">${esc(proj.title || "")} · 价值：${esc(s.value_before || "—")} → ${esc(s.value_after || "—")}</div>
    </div>
  </div>

  <div class="hook" style="margin-bottom:16px">
    <div class="q">${esc(s.hook || hook.question_left_open || "本集暂无钩子")}</div>
    <div class="meta">${esc(s.cliffhanger || hook.cliffhanger_type || "")} · ${esc(s.value_before || "")} → ${esc(s.value_after || "")}${hook.question_raised ? ` · 本集问题：${esc(hook.question_raised)}` : ""}</div>
  </div>

  <section class="panel" style="margin-bottom:16px">
    <h2>场景卡 <span class="small dim">${(d.cards || []).length} 场 · 预估 ${fmt(s.card_seconds)}s</span></h2>
    ${cards}
  </section>

  <section class="panel" style="margin-bottom:16px">
    <h2>剧本 <span class="small dim">${s.script_seconds ? s.script_seconds + "s" : "未写"}</span></h2>
    <div class="script">${md(d.script)}</div>
  </section>

  <section class="panel" style="margin-bottom:16px">
    <h2>集末状态 <span class="small dim">${Object.keys(chars).length} 人 · ${Object.keys(state.props || {}).length} 道具</span></h2>
    <div class="grid cols-2">${charCards}</div>
    ${props ? `<h3 style="margin:18px 0 8px">道具账本</h3>
      <table><thead><tr><th>道具</th><th>状态</th><th>持有者</th></tr></thead><tbody>${props}</tbody></table>` : ""}
    <div class="small dim" style="margin-top:10px">未回收伏笔：${esc((state.open_threads || []).join(", ") || "—")}</div>
  </section>

  <section class="panel">
    <h2>评审 <span class="small dim">${escapeRound(review)}</span></h2>
    ${review.summary ? `<div class="small muted" style="margin-bottom:14px">${md(review.summary)}</div>` : ""}
    ${scores || '<div class="empty-box">本集还没有评审</div>'}
    ${issues ? `<h3 style="margin:16px 0 8px">问题清单</h3>${issues}` : ""}
  </section>`;
}

function escapeRound(review) {
  const bits = [];
  if (review.round != null) bits.push(`round ${review.round}`);
  if (review.reviewer) bits.push(review.reviewer);
  if (review.verdict) bits.push(review.verdict);
  return esc(bits.join(" · "));
}

/* ---------------------------------------------------------------- 圣经 */
function renderBible(d) {
  const chars = (d.characters || []).map((c) => {
    const voice = (c.voice_samples || []).map((v) => `<li>“${esc(v)}”</li>`).join("") || "<li class='dim'>—</li>";
    const rules = (c.voice_rules || []).map((v) => `<li>${esc(v)}</li>`).join("");
    const never = (c.never_say || []).map((v) => `<li>${esc(v)}</li>`).join("");
    const prog = (c.progressions || []).map((p) => `<li><span class="mono">e${String(p.at).padStart(2, "0")}</span> ${esc(p.state)}</li>`).join("");
    return `<div class="char-card">
      <h3><span>${esc(c.name)}</span><span class="id">${esc(c.id)}</span></h3>
      <div class="row">${badge(c.role || "—", c.role === "protagonist" ? "accent" : "")}</div>
      <dl class="kv" style="margin-top:10px">
        <dt>欲望</dt><dd>${esc(c.want)}</dd>
        <dt>恐惧</dt><dd>${esc(c.fear)}</dd>
        <dt>秘密</dt><dd>${esc(c.secret)}</dd>
        <dt>谎言</dt><dd>${esc(c.lie)}</dd>
        <dt>创伤</dt><dd>${esc(c.wound)}</dd>
        <dt>弧光</dt><dd>${esc(c.arc)}</dd>
      </dl>
      <h4>声音样本</h4><ul>${voice}</ul>
      ${rules ? `<h4>声音规则</h4><ul>${rules}</ul>` : ""}
      ${never ? `<h4>绝不说</h4><ul>${never}</ul>` : ""}
      ${prog ? `<h4>时间线状态</h4><ul>${prog}</ul>` : ""}
    </div>`;
  }).join("") || '<div class="empty-box">暂无人物卡</div>';

  const relations = (d.relations || []).map((r) => `<tr>
      <td>${esc(r.from)} → ${esc(r.to)}</td>
      <td>${esc(r.type || "—")}</td>
      <td>${esc(r.power_diff || "—")}</td>
      <td>${esc(r.tension || "—")}</td>
      <td class="mono">${r.flip_episode ? "e" + String(r.flip_episode).padStart(2, "0") : "—"}</td>
    </tr>`).join("");

  return `
  <div class="page-head"><div><h1>故事圣经</h1><div class="sub">Premise · 人物 · 关系 · 世界 · 文风</div></div></div>
  <section class="panel" style="margin-bottom:16px"><h2>立意</h2><div>${md(d.premise)}</div></section>
  <section class="panel" style="margin-bottom:16px"><h2>人物 <span class="small dim">${(d.characters || []).length} 人</span></h2>
    <div class="grid cols-2">${chars}</div>
  </section>
  <section class="panel" style="margin-bottom:16px"><h2>关系网 <span class="small dim">${(d.relations || []).length} 条</span></h2>
    <table><thead><tr><th>关系</th><th>类型</th><th>权力差</th><th>张力</th><th>翻转集</th></tr></thead><tbody>${relations || '<tr><td colspan="5" class="dim">暂无</td></tr>'}</tbody></table>
  </section>
  <div class="grid cols-2">
    <section class="panel"><h2>世界规则</h2><div>${md(d.world)}</div></section>
    <section class="panel"><h2>文风与声音</h2><div>${md(d.voice)}</div></section>
  </div>`;
}

/* ---------------------------------------------------------------- 结构 */
function renderStructure(d) {
  const movements = (d.movements || []).map((m) => `
    <div class="movement">
      <div class="top"><span>乐章 ${m.id} · ${esc(m.name)}</span><span class="mono">${m.done}/${m.total}</span></div>
      <div class="goal">${esc(m.goal)}</div>
      <div class="bar"><i style="width:${m.percent}%"></i></div>
    </div>`).join("");

  const pinned = (d.pinned || []).map((p) => `<div class="scene">
      <div class="spread"><a class="sid" href="#/episode/${p.episode}">e${String(p.episode).padStart(2, "0")}</a>${badge(p.kind, "accent")}</div>
      <div class="obj">${esc(p.note)}</div>
    </div>`).join("");

  const hooks = (d.hooks || []).map((h) => `<tr>
      <td class="mono"><a href="#/episode/${h.episode}">e${String(h.episode).padStart(2, "0")}</a></td>
      <td>${esc(h.question_raised || "—")}</td>
      <td>${esc(h.question_left_open || "—")}</td>
      <td>${badge(h.cliffhanger_type || "—", "accent")}</td>
      <td class="small">${esc(h.value_before || "—")} → ${esc(h.value_after || "—")}</td>
      <td>${h.pinned ? "★" : ""}</td>
    </tr>`).join("");

  const threads = (d.threads || []).map((t) => `<tr>
      <td class="mono">${esc(t.id)}</td><td>${esc(t.desc)}</td>
      <td class="mono">e${String(t.plant).padStart(2, "0")}</td>
      <td class="mono">e${String(t.payoff).padStart(2, "0")}</td>
      <td>${esc(t.state)}</td><td class="small dim">${esc(t.note || "")}</td>
    </tr>`).join("");

  return `
  <div class="page-head"><div><h1>结构</h1><div class="sub">五乐章 · 钉死集 · 70 集钩子表 · 伏笔账本</div></div></div>
  <div class="grid cols-2" style="margin-bottom:16px">
    <section class="panel"><h2>五乐章</h2>${movements}</section>
    <section class="panel"><h2>钉死集</h2>${pinned || '<div class="empty-box">暂无</div>'}</section>
  </div>
  <section class="panel" style="margin-bottom:16px">
    <h2>钩子表</h2>
    <div style="max-height:620px;overflow:auto">
      <table><thead><tr><th>集</th><th>本集问题</th><th>集末问题</th><th>悬念</th><th>价值线</th><th>钉</th></tr></thead><tbody>${hooks}</tbody></table>
    </div>
  </section>
  <section class="panel"><h2>伏笔账本</h2>
    <table><thead><tr><th>ID</th><th>伏笔</th><th>埋设</th><th>回收</th><th>状态</th><th>备注</th></tr></thead><tbody>${threads}</tbody></table>
  </section>`;
}

/* ---------------------------------------------------------------- 连续性 */
function renderContinuity(d) {
  const issues = (d.issues || []).map((i) => `<div class="issue ${i.level}">
      <span class="rule">${esc(i.rule || "")}</span>
      <div>${esc(i.msg || "")}</div>
      ${i.loc ? `<div class="small dim">${esc(i.loc)}</div>` : ""}
    </div>`).join("") || '<div class="empty-box">未发现跨集 Continuity 问题</div>';

  const eps = (d.episodes || []).map((e) => `<tr>
      <td class="mono">e${String(e.ep).padStart(2, "0")}</td>
      <td class="mono">${e.script_seconds}s</td>
      <td class="mono">${fmt(e.review_total)}/${fmt(e.review_threshold)}</td>
      <td>${esc(e.review_verdict || "—")}</td>
      <td class="small">${e.locations.map((l) => `${esc(l.id)}:${esc(l.location)}`).join("；") || "—"}</td>
      <td class="mono">${e.props}</td>
      <td class="small">${esc((e.open_threads || []).join(", ") || "—")}</td>
    </tr>`).join("");

  return `
  <div class="page-head">
    <div><h1>连续性巡检</h1><div class="sub">已进入制作 ${d.latest} 集 · K1–K8 跨集检查</div></div>
    <div class="row">
      ${badge(`BLOCKER ${(d.blockers || []).length}`, (d.blockers || []).length ? "bad" : "ok")}
      ${badge(`WARN ${(d.warnings || []).length}`, (d.warnings || []).length ? "warn" : "ok")}
    </div>
  </div>
  <section class="panel" style="margin-bottom:16px"><h2>问题清单</h2>${issues}</section>
  <section class="panel"><h2>集末状态账本</h2>
    <div style="overflow:auto"><table><thead><tr><th>集</th><th>秒</th><th>评审</th><th>结论</th><th>人物位置</th><th>道具</th><th>open_threads</th></tr></thead><tbody>${eps}</tbody></table></div>
  </section>`;
}

/* ---------------------------------------------------------------- 决策 */
function renderDecisions(d) {
  const items = (d.decisions || []).map((x) => {
    const alts = Array.isArray(x.alternatives) ? x.alternatives.map((a) => `<span class="badge">${esc(a)}</span>`).join(" ") : "";
    return `<div class="tl-item">
      <div class="ts">${esc(x.ts || "")}</div>
      <div class="act">${x.episode ? `e${String(x.episode).padStart(2, "0")} · ` : ""}${esc(x.stage || "")} · ${esc(x.action || "")}</div>
      <div class="reason">${esc(x.chosen || "")}</div>
      ${x.reason ? `<div class="reason dim" style="margin-top:3px">${esc(x.reason)}</div>` : ""}
      ${alts ? `<div class="row" style="margin-top:6px">${alts}</div>` : ""}
    </div>`;
  }).join("") || '<div class="empty-box">暂无决策记录</div>';

  return `
  <div class="page-head"><div><h1>决策日志</h1><div class="sub">共 ${d.total} 条 · 追加式，后续创作必须尊重</div></div></div>
  <section class="panel"><div class="timeline">${items}</div></section>`;
}

/* ---------------------------------------------------------------- 启动 */
async function init() {
  $("#refresh-btn").addEventListener("click", () => { route(); toast("已重新读取磁盘"); });
  $("#project-select").addEventListener("change", (e) => {
    state.slug = e.target.value;
    localStorage.setItem("storylab.slug", state.slug);
    location.hash = "#/overview";
    route();
  });
  window.addEventListener("hashchange", route);

  try {
    const health = await api("/api/health");
    $("#health-dot").className = "dot ok";
    const res = await api("/api/projects");
    state.projects = res.projects || [];
    const sel = $("#project-select");
    sel.innerHTML = state.projects.map((p) =>
      `<option value="${esc(p.slug)}">${esc(p.title)}（${esc(p.slug)}）</option>`).join("");
    const saved = localStorage.getItem("storylab.slug");
    state.slug = state.projects.some((p) => p.slug === saved) ? saved : (state.projects[0] || {}).slug;
    if (!state.slug) {
      app.innerHTML = '<div class="panel"><h2>没有找到项目</h2><p class="muted">请在 projects/ 下创建故事项目。</p></div>';
      return;
    }
    sel.value = state.slug;
    if (!location.hash) location.hash = "#/overview";
    route();
  } catch (err) {
    $("#health-dot").className = "dot bad";
    app.innerHTML = `<div class="panel"><h2>无法连接服务</h2><p class="muted">${esc(err.message)}</p></div>`;
  }
}

init();
