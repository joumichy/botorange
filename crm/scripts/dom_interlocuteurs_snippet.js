(async () => {
    // --- utilitaires ---
    const clean = t => t ? t.trim().replace(/\s+/g, " ") : "";
    const digits = t => clean(t).replace(/[^\d+]/g, "");
    const normalize = t => clean(t).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    const wait = t => new Promise(res => setTimeout(res, t));
  
    // mots-clés recherchés
    const keywords = ["direction", "gerant", "dirigeant", "ressource"].map(normalize);
  
    // parsing nom complet
    const parseName = t => {
      const name = clean(t).replace(/^(M\.|Mme|Mlle|Mr|Ms|Dr)\.?\s*/i, "");
      const parts = name.split(" ").filter(Boolean);
      if (!parts.length) return { firstName: "", lastName: "" };
      if (parts.length === 1) return { firstName: parts[0], lastName: "" };
      return parts[0] === parts[0].toUpperCase()
        ? { firstName: parts.slice(1).join(" "), lastName: parts[0][0] + parts[0].slice(1).toLowerCase() }
        : { firstName: parts[0], lastName: parts.slice(1).join(" ") };
    };
  
    // fonction principale d’extraction sur une page
    const extract = () => {
      const items = document.querySelectorAll(".accordion-item.inter");
      const seen = new Set();
      const results = [];
  
      items.forEach(item => {
        const funcNode = Array.from(item.querySelectorAll(".inter-item-title"))
          .find(el => normalize(el.textContent).startsWith("fonction"));
        const fonction = clean(funcNode?.nextElementSibling?.textContent || "");
        if (!fonction) return;
  
        const match = keywords.some(k => normalize(fonction).includes(k));
  
        const nameEl = item.querySelector("[id^='name-']") ||
                       item.querySelector(".accordion-button [id^='name-']") ||
                       item.querySelector(".accordion-button");
        const mailEl = item.querySelector("[id^='mail-'] a") || item.querySelector("[id^='mail-']");
        const mobEl = item.querySelector("[id^='mobile-']");
        const fixEl = item.querySelector("[id^='fixe-']");
  
        const name = clean(nameEl?.textContent || "");
        const { firstName, lastName } = parseName(name);
        const emailRaw = clean(mailEl?.textContent || mailEl?.getAttribute?.("href") || "");
        const email = emailRaw.startsWith("mailto:") ? emailRaw.replace(/^mailto:/i, "") : emailRaw;
        const mobile = digits(mobEl?.textContent || "");
        const fixe = digits(fixEl?.textContent || "");
  
        const unique = email ? `e:${normalize(email)}` :
          `n:${normalize(firstName)}-${normalize(lastName)}|m:${mobile}|f:${fixe}`;
  
        if (seen.has(unique)) return;
        seen.add(unique);
  
        results.push({
          firstName, lastName, email, mobile, fixe, fonction,
          category: match ? "Ciblé" : "Autre"
        });
      });
  
      return results;
    };
  
    // --- boucle sur toutes les pages ---
    const all = [];
    let page = 1;
    for (;;) {
      console.info("📄 page", page);
      all.push(...extract());
      const next = document.querySelector("li.page-item:not(.disabled) a[aria-label='Next']");
      if (!next) { console.info("✅ fin"); break; }
      next.click();
      page++;
      await wait(3000); // ⏱️ pause de 3 secondes entre les pages
    }
  
    // filtrage final
    const targeted = all.filter(x => x.category === "Ciblé");
    const others = all.filter(x => x.category === "Autre").slice(0, 3);
    const final = [...targeted, ...others];
  
    console.table(final);
    const json = JSON.stringify(final, null, 2);
    prompt(`📋 ${final.length} contact(s) (dont 3 "Autre")\nCtrl+C puis Entrée:`, json);
    window.close();
  })();
  