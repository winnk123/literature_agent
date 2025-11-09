(function () {
  const qs = (s, r = document) => r.querySelector(s);
  const qsa = (s, r = document) => Array.from(r.querySelectorAll(s));

  const homeView = qs('#home-view');
  const detailView = qs('#detail-view');
  const searchInput = qs('#searchInput');
  const searchBtn = qs('#searchBtn');
  const loginModal = qs('#loginModal');
  const closeModal = qs('#closeModal');
  const featureBar = qs('#featureBar');
  const currentRoleEl = qs('#currentRole');
  const createProblemBtn = qs('#createProblemBtn');
  const uploadDataBtn = qs('#uploadDataBtn');
  const logoutBtn = qs('#logoutBtn');
  const homeNavBtn = qs('#homeNavBtn');
  const projectsNavBtn = qs('#projectsNavBtn');
  const createNavBtn = qs('#createNavBtn');
  const homeHero = qs('#homeHero');
  const projectsView = qs('#projectsView');
  const projectsGrid = qs('#projectsGrid');

  let currentUserRole = null;

  const themeToggles = [qs('#themeToggle'), qs('#themeToggle2')].filter(Boolean);
  themeToggles.forEach(btn => btn.addEventListener('click', () => {
    document.body.classList.toggle('theme-dark');
    document.body.classList.toggle('theme-light');
  }));

  // 密集粒子云特效
  function createDenseParticleCloud() {
    const particleBox = qs('#particleBox');
    const particleTextOverlay = qs('#particleTextOverlay');
    if (!particleBox || !particleTextOverlay) return;

    const fullText = '有你想学习的任何东西';
    const textArray = fullText.split('');
    
    // 清空粒子容器
    particleBox.innerHTML = '';
    
    // 获取文字尺寸和位置
    const fontSize = window.innerWidth <= 680 ? '20px' : '32px';
    particleTextOverlay.style.fontSize = fontSize;
    
    const tempSpan = document.createElement('span');
    tempSpan.textContent = fullText;
    tempSpan.style.cssText = `position: absolute; visibility: hidden; font-size: ${fontSize}; font-weight: 800; white-space: nowrap; font-family: "Inter", ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Noto Sans", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;`;
    document.body.appendChild(tempSpan);
    const textWidth = tempSpan.offsetWidth;
    const textHeight = tempSpan.offsetHeight || 40;
    document.body.removeChild(tempSpan);
    
    // 计算每个字符的位置
    const charPositions = [];
    const charWidth = textWidth / textArray.length;
    const boxWidth = particleBox.offsetWidth;
    const boxHeight = particleBox.offsetHeight;
    const startX = (boxWidth - textWidth) / 2;
    const startY = (boxHeight - textHeight) / 2;
    
    textArray.forEach((char, index) => {
      if (char === ' ') return;
      const charX = startX + (index * charWidth) + (charWidth / 2);
      const charY = startY + textHeight / 2;
      charPositions.push({ x: charX, y: charY, char: char });
    });
    
    // 创建大量密集粒子
    const totalParticles = 1200; // 更密集的粒子数量
    const particles = [];
    
    // 为每个字符分配粒子
    const particlesPerChar = Math.floor(totalParticles / charPositions.length);
    
    charPositions.forEach((charPos, charIndex) => {
      for (let i = 0; i < particlesPerChar; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        // 随机初始位置（在盒子内，但可以稍微集中在中心）
        const randomX = Math.random() * boxWidth;
        const randomY = Math.random() * boxHeight;
        
        // 随机大小和透明度（更小的粒子，更密集）
        const size = 1.5 + Math.random() * 1.5;
        const opacity = 0.6 + Math.random() * 0.3;
        
        // 初始状态：粒子在盒子内随机位置，但会被重置到外部
        particle.style.cssText = `
          width: ${size}px;
          height: ${size}px;
          opacity: 0;
          transform: scale(0);
        `;
        
        particleBox.appendChild(particle);
        particles.push({
          element: particle,
          startX: 0, // 将在后面设置为外部位置
          startY: 0, // 将在后面设置为外部位置
          startSize: size,
          startOpacity: opacity,
          targetX: charPos.x,
          targetY: charPos.y,
          charIndex: charIndex
        });
      }
    });
    
    // 添加剩余的粒子（随机分布）
    const remaining = totalParticles - (particlesPerChar * charPositions.length);
    for (let i = 0; i < remaining; i++) {
      const particle = document.createElement('div');
      particle.className = 'particle';
      const randomX = Math.random() * boxWidth;
      const randomY = Math.random() * boxHeight;
      const size = 1.5 + Math.random() * 1.5;
      const opacity = 0.6 + Math.random() * 0.3;
      
      // 初始状态：粒子在盒子内随机位置，但会被重置到外部
      particle.style.cssText = `
        width: ${size}px;
        height: ${size}px;
        opacity: 0;
        transform: scale(0);
      `;
      
      particleBox.appendChild(particle);
      const randomCharIndex = Math.floor(Math.random() * charPositions.length);
      particles.push({
        element: particle,
        startX: 0, // 将在后面设置为外部位置
        startY: 0, // 将在后面设置为外部位置
        startSize: size,
        startOpacity: opacity,
        targetX: charPositions[randomCharIndex].x,
        targetY: charPositions[randomCharIndex].y,
        charIndex: randomCharIndex
      });
    }
    
    // 移除浮动动画，使用AE风格的飞入动画
    
    // AE风格文字粒子出现动画
    let isAnimating = false;
    let animationFrame = null;
    
    // 初始化粒子位置（在盒子外部随机位置）
    particles.forEach((p) => {
      // 随机起始位置（盒子外部）
      const side = Math.floor(Math.random() * 4); // 0:上, 1:右, 2:下, 3:左
      let startX, startY;
      
      switch(side) {
        case 0: // 上方
          startX = Math.random() * boxWidth;
          startY = -20 - Math.random() * 30;
          break;
        case 1: // 右侧
          startX = boxWidth + 20 + Math.random() * 30;
          startY = Math.random() * boxHeight;
          break;
        case 2: // 下方
          startX = Math.random() * boxWidth;
          startY = boxHeight + 20 + Math.random() * 30;
          break;
        case 3: // 左侧
          startX = -20 - Math.random() * 30;
          startY = Math.random() * boxHeight;
          break;
      }
      
      p.startX = startX;
      p.startY = startY;
      p.element.style.left = `${startX}px`;
      p.element.style.top = `${startY}px`;
      p.element.style.opacity = '0';
      p.element.style.transform = 'scale(0)';
    });
    
    // 粒子飞入动画函数
    function animateParticlesIn() {
      if (isAnimating) return;
      isAnimating = true;
      particleBox.classList.add('contracting');
      
      // 按字符顺序，粒子依次飞入
      charPositions.forEach((charPos, charIndex) => {
        const charParticles = particles.filter(p => p.charIndex === charIndex);
        
        charParticles.forEach((p, pIndex) => {
          // AE风格的延迟：按字符顺序，每个字符内的粒子有随机延迟
          const baseDelay = charIndex * 0.08; // 每个字符基础延迟
          const particleDelay = (pIndex / charParticles.length) * 0.12; // 粒子间延迟
          const randomDelay = Math.random() * 0.05; // 随机微调
          const totalDelay = (baseDelay + particleDelay + randomDelay) * 1000;
          
          setTimeout(() => {
            // 计算飞入轨迹（带轻微曲线）
            const dx = p.targetX - p.startX;
            const dy = p.targetY - p.startY;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            // 添加轻微曲线效果
            const curveOffset = distance * 0.1;
            const midX = (p.startX + p.targetX) / 2 + (Math.random() - 0.5) * curveOffset;
            const midY = (p.startY + p.targetY) / 2 + (Math.random() - 0.5) * curveOffset;
            
            // 使用关键帧动画实现飞入效果
            const keyframes = `
              @keyframes flyIn${p.element.dataset.index} {
                0% {
                  left: ${p.startX}px;
                  top: ${p.startY}px;
                  transform: scale(0) rotate(0deg);
                  opacity: 0;
                }
                50% {
                  left: ${midX}px;
                  top: ${midY}px;
                  transform: scale(1.2) rotate(180deg);
                  opacity: 0.8;
                }
                100% {
                  left: ${p.targetX}px;
                  top: ${p.targetY}px;
                  transform: scale(0.4) rotate(360deg);
                  opacity: 0.3;
                }
              }
            `;
            
            // 添加动画样式
            if (!document.getElementById(`flyInStyle${p.element.dataset.index}`)) {
              const style = document.createElement('style');
              style.id = `flyInStyle${p.element.dataset.index}`;
              style.textContent = keyframes;
              document.head.appendChild(style);
            }
            
            p.element.style.animation = `flyIn${p.element.dataset.index} 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards`;
            p.element.style.transition = 'none';
          }, totalDelay);
        });
      });
      
      // 文字淡入（在粒子开始汇聚后）
      setTimeout(() => {
        particleTextOverlay.style.opacity = '1';
        particleTextOverlay.style.transform = 'scale(1)';
      }, charPositions.length * 0.08 * 1000 + 400);
    }
    
    // 粒子散开动画
    function animateParticlesOut() {
      if (!isAnimating) return;
      isAnimating = false;
      particleBox.classList.remove('contracting');
      
      // 文字淡出
      particleTextOverlay.style.opacity = '0';
      particleTextOverlay.style.transform = 'scale(0.8)';
      
      // 粒子散开
      particles.forEach((p, index) => {
        const delay = (index % 40) * 0.01;
        
        setTimeout(() => {
          // 随机散开方向
          const angle = Math.random() * Math.PI * 2;
          const distance = 50 + Math.random() * 50;
          const endX = p.targetX + Math.cos(angle) * distance;
          const endY = p.targetY + Math.sin(angle) * distance;
          
          p.element.style.animation = 'none';
          p.element.style.transition = 'all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
          p.element.style.left = `${endX}px`;
          p.element.style.top = `${endY}px`;
          p.element.style.transform = 'scale(0)';
          p.element.style.opacity = '0';
          
          // 散开后重置到起始位置
          setTimeout(() => {
            p.element.style.transition = 'none';
            p.element.style.left = `${p.startX}px`;
            p.element.style.top = `${p.startY}px`;
          }, 600);
        }, delay * 1000);
      });
    }
    
    // 鼠标事件
    particleBox.addEventListener('mouseenter', animateParticlesIn);
    particleBox.addEventListener('mouseleave', animateParticlesOut);
  }

  // 创建高科技粒子效果
  function createTechParticles() {
    const hero = qs('.hero');
    if (!hero) return;

    const particlesContainer = qs('.hero__bg-particles');
    if (!particlesContainer) return;

    // 清除已存在的粒子
    const existingParticles = particlesContainer.querySelectorAll('.tech-particle');
    existingParticles.forEach(p => p.remove());

    // 添加基础粒子动画样式
    if (!document.getElementById('particleStyles')) {
      const style = document.createElement('style');
      style.id = 'particleStyles';
      style.textContent = `
        @keyframes particleFloat {
          0%, 100% {
            transform: translate(0, 0) scale(1);
            opacity: 0.3;
          }
          25% {
            transform: translate(30px, -30px) scale(1.2);
            opacity: 0.6;
          }
          50% {
            transform: translate(-20px, 20px) scale(0.8);
            opacity: 0.4;
          }
          75% {
            transform: translate(20px, 30px) scale(1.1);
            opacity: 0.7;
          }
        }
        @keyframes particleFloat2 {
          0%, 100% {
            transform: translate(0, 0) scale(1);
            opacity: 0.2;
          }
          25% {
            transform: translate(-40px, 20px) scale(1.3);
            opacity: 0.5;
          }
          50% {
            transform: translate(25px, -25px) scale(0.9);
            opacity: 0.3;
          }
          75% {
            transform: translate(-15px, -35px) scale(1.15);
            opacity: 0.6;
          }
        }
        @keyframes particleFloat3 {
          0%, 100% {
            transform: translate(0, 0) scale(1);
            opacity: 0.25;
          }
          25% {
            transform: translate(35px, 25px) scale(1.1);
            opacity: 0.55;
          }
          50% {
            transform: translate(-30px, -20px) scale(0.85);
            opacity: 0.35;
          }
          75% {
            transform: translate(15px, 40px) scale(1.2);
            opacity: 0.65;
          }
        }
      `;
      document.head.appendChild(style);
    }

    // 创建多个小粒子
    const animations = ['particleFloat', 'particleFloat2', 'particleFloat3'];
    for (let i = 0; i < 20; i++) {
      const particle = document.createElement('div');
      const size = Math.random() * 4 + 2;
      const left = Math.random() * 100;
      const top = Math.random() * 100;
      const duration = 10 + Math.random() * 20;
      const delay = Math.random() * 5;
      const animIndex = Math.floor(Math.random() * animations.length);
      
      particle.className = 'tech-particle';
      particle.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        background: linear-gradient(135deg, rgba(160, 82, 45, 0.5), rgba(139, 69, 19, 0.5));
        border-radius: 50%;
        left: ${left}%;
        top: ${top}%;
        animation: ${animations[animIndex]} ${duration}s infinite ease-in-out;
        animation-delay: ${delay}s;
        box-shadow: 0 0 ${Math.random() * 6 + 2}px rgba(160, 82, 45, 0.4);
        pointer-events: none;
      `;
      particlesContainer.appendChild(particle);
    }
  }

  // 添加文字光晕效果
  function addTextGlow() {
    const particleTextOverlay = qs('#particleTextOverlay');
    if (!particleTextOverlay) return;

    // 添加文字发光动画
    const style = document.createElement('style');
    style.id = 'textGlowStyles';
    style.textContent = `
      @keyframes textGlow {
        0%, 100% {
          text-shadow: 0 0 10px rgba(160, 82, 45, 0.3),
                       0 0 20px rgba(160, 82, 45, 0.2),
                       0 0 30px rgba(139, 69, 19, 0.1);
        }
        50% {
          text-shadow: 0 0 15px rgba(160, 82, 45, 0.5),
                       0 0 30px rgba(160, 82, 45, 0.3),
                       0 0 45px rgba(139, 69, 19, 0.2);
        }
      }
      .particle-text-overlay {
        animation: textGlow 3s ease-in-out infinite;
      }
    `;
    document.head.appendChild(style);
  }

  // 扇形展开特效（放慢节奏）
  function initFanSpreadAnimation() {
    const fanElement = qs('#learnEveryHere');
    if (!fanElement) return;

    // 将文字拆分成单个字符
    const text = fanElement.textContent.trim();
    fanElement.innerHTML = '';
    
    const chars = text.split('');
    const totalChars = chars.length;
    const centerIndex = Math.floor(totalChars / 2);
    
    // 为每个字符创建span，并设置延迟和旋转角度（扇形展开）
    chars.forEach((char, index) => {
      const span = document.createElement('span');
      span.textContent = char === '\u0020' ? '\u00A0' : char; // 空格用不间断空格
      
      // 计算相对于中心的位置，创建扇形效果
      const offsetFromCenter = index - centerIndex;
      const maxAngle = 20; // 更柔和
      const initialAngle = centerIndex > 0 ? (offsetFromCenter / centerIndex) * maxAngle : 0;
      const delay = Math.abs(offsetFromCenter) * 0.12; // 更慢
      
      span.style.animationDelay = `${delay}s`;
      span.style.setProperty('--initial-angle', `${initialAngle}deg`);
      fanElement.appendChild(span);
    });

    // 注入更慢的动画样式
    const existing = document.getElementById('fanSpreadStyles');
    if (existing) existing.remove();
    const style = document.createElement('style');
    style.id = 'fanSpreadStyles';
    style.textContent = `
      .hero__title-fan.fan-animate span {
        animation: fanSpreadVar 1.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
      }
      @keyframes fanSpreadVar {
        0% {
          opacity: 0;
          transform: rotate(calc(var(--initial-angle, 0deg) - 50deg)) translateY(100px) scale(0.2);
        }
        50% {
          opacity: 0.9;
          transform: rotate(calc(var(--initial-angle, 0deg) + 5deg)) translateY(-15px) scale(1.2);
        }
        100% {
          opacity: 1;
          transform: rotate(0deg) translateY(0) scale(1);
        }
      }
    `;
    document.head.appendChild(style);

    // 触发动画
    setTimeout(() => {
      fanElement.classList.add('fan-animate');
    }, 200);
  }

  // 初始化动画效果
  function initAnimations() {
    const particleBox = qs('#particleBox');
    if (particleBox && !particleBox.dataset.animated) {
      particleBox.dataset.animated = 'true';
      createDenseParticleCloud();
      createTechParticles();
      addTextGlow();
    }

    // 初始化扇形展开动画
    initFanSpreadAnimation();
  }

  // 页面加载完成后初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      if (homeView && homeView.classList.contains('active')) {
        initAnimations();
      }
      showHomeView();
    });
  } else {
    if (homeView && homeView.classList.contains('active')) {
      initAnimations();
    }
    showHomeView();
  }

  // 监听视图切换，在首页显示时启动动画
  const observer = new MutationObserver(() => {
    if (homeView && homeView.classList.contains('active')) {
      initAnimations();
    }
  });
  if (homeView) observer.observe(homeView, { attributes: true, attributeFilter: ['class'] });

  // 绑定侧边导航
  if (homeNavBtn) homeNavBtn.addEventListener('click', showHomeView);
  if (projectsNavBtn) projectsNavBtn.addEventListener('click', showProjectsView);
  if (createNavBtn) createNavBtn.addEventListener('click', () => {
    if (createProblemBtn) {
      createProblemBtn.click();
    } else if (loginModal) {
      loginModal.classList.add('active');
    }
  });

  // 分类与项目数据
  const categories = [
    { key: 'image', name: '图像', items: [
      { key: 'cam-denoise', name: '相机的图像去噪' },
      { key: 'photo-restore', name: '照片的图像修复' }
    ]},
    { key: 'audio', name: '语音', items: [
      { key: 'speech-enhance', name: '语音增强' },
      { key: 'speech-separate', name: '语音分离' }
    ]},
    { key: 'llm', name: 'LLM', items: [
      { key: 'knowledge-retrieval', name: '知识检索' },
      { key: 'code-assistant', name: '代码助手' }
    ]},
    { key: 'mllm', name: 'MLLM', items: [
      { key: 'vision-language', name: '图文理解' }
    ]},
    { key: 'agent', name: 'Agent', items: [
      { key: 'research-agent', name: '科研助手' }
    ]}
  ];

  const projects = [
    { id: 'p1', category: 'image', subKey: 'cam-denoise', title: '相机的图像去噪 · 实验版', desc: '复杂背景下的高保真去噪。', likes: 128 },
    { id: 'p6', category: 'image', subKey: 'photo-restore', title: '照片的图像修复 · 划痕', desc: '老照片划痕修复与细节重建。', likes: 64 },
    { id: 'p2', category: 'audio', subKey: 'speech-enhance', title: '语音增强 · 远场', desc: '远场语音的清晰化处理。', likes: 76 },
    { id: 'p7', category: 'audio', subKey: 'speech-separate', title: '语音分离 · 鸣噪', desc: '音乐与语音的自适应分离。', likes: 58 },
    { id: 'p3', category: 'llm', subKey: 'knowledge-retrieval', title: 'LLM · 知识检索', desc: '检索增强生成。', likes: 203 },
    { id: 'p8', category: 'llm', subKey: 'code-assistant', title: 'LLM · 代码助手', desc: '上下文感知的编程辅助。', likes: 312 },
    { id: 'p4', category: 'mllm', subKey: 'vision-language', title: 'MLLM · 图文理解', desc: '多模态语义对齐与问答。', likes: 97 },
    { id: 'p5', category: 'agent', subKey: 'research-agent', title: 'Agent · 科研助手', desc: '工作流编排与自动化研究。', likes: 141 }
  ];

  // 渲染项目卡片到 projectsGrid
  function renderCards(list) {
    if (!projectsGrid) return;
    projectsGrid.innerHTML = '';
    list.forEach(p => {
      const card = document.createElement('div');
      card.className = 'card';
      card.setAttribute('data-id', p.id);
      card.innerHTML = `
        <div class="card__poster">${p.category.toUpperCase()}<span class="badge">精选</span></div>
        <div class="card__body">
          <div class="card__title">${p.title}</div>
          <div class="card__desc">${p.desc}</div>
          <div class="card__meta"><span class="thumb">👍 ${p.likes}</span></div>
        </div>
      `;
      card.addEventListener('click', () => openDetail(p));
      projectsGrid.appendChild(card);
    });
  }

  function setPrimaryNavActive(btn) {
    [homeNavBtn, projectsNavBtn].forEach(b => b && b.classList.remove('is-active'));
    if (btn) btn.classList.add('is-active');
  }

  function showHomeView() {
    setPrimaryNavActive(homeNavBtn);
    if (homeHero) homeHero.style.display = '';
    if (projectsView) {
      projectsView.classList.remove('is-active');
      projectsView.style.display = 'none';
    }
    if (projectsGrid) projectsGrid.innerHTML = '';
    initFanSpreadAnimation();
  }

  function showProjectsView() {
    setPrimaryNavActive(projectsNavBtn);
    if (homeHero) homeHero.style.display = 'none';
    if (projectsView) {
      projectsView.classList.add('is-active');
      projectsView.style.display = '';
    }
    renderCards(projects);
  }

  // 渲染左侧分类（可展开）
  const categoryList = document.getElementById('categoryList');
  function renderCategories() {
    if (!categoryList) return;
    categoryList.innerHTML = '';
    // “全部”
    const allLi = document.createElement('li');
    allLi.innerHTML = `<button class="nav__item is-active" data-category="all"><span class="caret">◆</span>全部</button>`;
    categoryList.appendChild(allLi);
    allLi.querySelector('button').addEventListener('click', () => {
      Array.from(categoryList.querySelectorAll('.nav__item')).forEach(b => b.classList.remove('is-active'));
      allLi.querySelector('button').classList.add('is-active');
      categoryList.querySelectorAll('.sublist').forEach(u => u.remove());
      renderCards(projects);
    });

    categories.forEach(cat => {
      const li = document.createElement('li');
      li.innerHTML = `<button class=\"nav__item\" data-category=\"${cat.key}\"><span class=\"caret\">▸</span>${cat.name}</button>`;
      const btn = li.querySelector('button');
      btn.addEventListener('click', () => toggleCategory(li, cat));
      categoryList.appendChild(li);
    });
  }

  function toggleCategory(li, cat) {
    Array.from(categoryList.querySelectorAll('.nav__item')).forEach(b => b.classList.remove('is-active'));
    const btn = li.querySelector('.nav__item');
    btn.classList.add('is-active');

    const opened = li.querySelector('.sublist');
    categoryList.querySelectorAll('.sublist').forEach(u => u.remove());
    Array.from(categoryList.querySelectorAll('.caret')).forEach(c => c.textContent = '▸');
    if (!opened) {
      btn.querySelector('.caret').textContent = '▾';
      const ul = document.createElement('ul');
      ul.className = 'sublist';
      cat.items.forEach(sub => {
        const subLi = document.createElement('li');
        subLi.innerHTML = `<button class=\"subitem\" data-sub=\"${sub.key}\">${sub.name}</button>`;
        subLi.querySelector('button').addEventListener('click', (e) => {
          e.stopPropagation();
          renderCards(projects.filter(p => p.category === cat.key && p.subKey === sub.key));
        });
        ul.appendChild(subLi);
      });
      li.appendChild(ul);
      renderCards(projects.filter(p => p.category === cat.key));
    } else {
      renderCards(projects);
    }
  }

  function openDetail(project) {
    buildDetailMenu(project);

    const titleEl = document.getElementById('projectTitle');
    if (titleEl) titleEl.textContent = '';
    const bc = document.querySelector('.detail__breadcrumbs');
    if (bc) bc.textContent = `${project.category.toUpperCase()} · ${project.title.split('·')[0].trim()}`;

    renderDetailSection('background');
    switchView('detail');
    history.pushState({ view: 'detail', id: project.id, section: 'background' }, '', `#project/${project.id}/background`);
  }

  function buildDetailMenu(project) {
    const menu = document.getElementById('detailMenu');
    menu.innerHTML = '';
    const groups = [
      { key: 'background', name: '背景' },
      { key: 'model', name: '模型', children: [
        { key: 'model-intro', name: '模型介绍' },
        { key: 'baseline', name: 'baseline 介绍' }
      ]},
      { key: 'idea', name: 'IDEA 引导' },
      { key: 'personalize', name: '个性化检验' },
      { key: 'comments', name: '留言区' }
    ];

    const ul = document.createElement('ul');
    ul.className = 'nav__list';
    groups.forEach(g => {
      const li = document.createElement('li');
      li.innerHTML = `<button class=\"nav__item\" data-sec=\"${g.key}\"><span class=\"caret\">${g.children ? '▸' : '◆'}</span>${g.name}</button>`;
      const btn = li.querySelector('button');
      if (g.children) {
        btn.addEventListener('click', () => {
          const opened = li.querySelector('.sublist');
          li.querySelector('.caret').textContent = opened ? '▸' : '▾';
          if (opened) { opened.remove(); return; }
          const sub = document.createElement('ul');
          sub.className = 'sublist';
          g.children.forEach(c => {
            const sli = document.createElement('li');
            sli.innerHTML = `<button class=\"subitem\" data-sec=\"${c.key}\">${c.name}</button>`;
            sli.querySelector('button').addEventListener('click', (e) => {
              e.stopPropagation();
              renderDetailSection(c.key);
              history.pushState({ view: 'detail', id: project.id, section: c.key }, '', `#project/${project.id}/${c.key}`);
            });
            sub.appendChild(sli);
          });
          li.appendChild(sub);
        });
      } else {
        btn.addEventListener('click', () => {
          renderDetailSection(g.key);
          history.pushState({ view: 'detail', id: project.id, section: g.key }, '', `#project/${project.id}/${g.key}`);
        });
      }
      ul.appendChild(li);
    });
    menu.appendChild(ul);
  }

  function renderDetailSection(key) {
    const wrap = document.getElementById('detailContent');
    const templates = {
      'background': `<h3>背景</h3>
        <p>在真实相机成像链路中，噪声来源包括读出噪声、光子噪声以及 ISP 处理引入的复合噪声。低照度、运动模糊与复杂背景进一步放大噪声影响，导致细节丢失与纹理伪影。</p>
        <ul>
          <li>数据来源：合成+真实数据集（DND、SIDD、自采样室内外场景）。</li>
          <li>任务目标：在保持结构一致性的前提下提升 PSNR/SSIM，并兼顾 LPIPS 感知质量。</li>
          <li>难点：弱光噪声分布不均、跨设备域泛化、速度与质量的平衡。</li>
        </ul>
        <h4>方案概览</h4>
        <p>采用多尺度 U-Net 主干，结合噪声估计支路与频域残差补偿；训练阶段引入合成+真实的混合噪声建模与自蒸馏策略。</p>` ,
      'model': `<h3>模型</h3>
        <p>整体结构为 Encoder-Decoder 框架，带跨层跳连与注意力模块。引入噪声水平预测头用于动态调节去噪强度。</p>
        <ul>
          <li>损失函数：L1 + SSIM + Perceptual（三者加权）。</li>
          <li>训练细节：Cosine LR、混合精度、随机裁剪 256×256。</li>
          <li>推理：Tile-Sliding 支持超大分辨率图像。</li>
        </ul>`,
      'model-intro': `<h3>模型介绍</h3><p>包含自适应门控注意力（AGA）模块与频域残差增强（FRE）模块，前者缓解细节过平滑，后者针对高频纹理恢复。</p>`,
      'baseline': `<h3>baseline 介绍</h3><p>对比 BM3D、DnCNN、RIDNet、NAFNet 等，指标与耗时均衡下取得最佳 LPIPS/PSNR。</p>`,
      'idea': `<h3>IDEA 引导</h3>
        <ul>
          <li>数据：合成噪声混入相机 ISP 模拟过程，增强真实度。</li>
          <li>结构：探索轻量 Transformer 模块以替换部分卷积层。</li>
          <li>指标：引入 NR-IQA 作为辅助优化目标。</li>
        </ul>`,
      'personalize': `<h3>个性化检验</h3><ul><li>样本对比：上传原图/噪声图，自动生成前后对比。</li><li>参数扫描：强度、频域权重、tile 步长。</li><li>鲁棒性：动态范围/场景光比测试。</li></ul>`,
      'comments': `<h3>留言区</h3><div class=\"comments\"><div class=\"comment\"><b>研究者A：</b>期待开源！</div><div class=\"comment\"><b>研究者B：</b>建议补充低光场景。</div></div>`
    };
    wrap.innerHTML = templates[key] || `<p>即将上线…</p>`;
  }

  function switchView(view) {
    const toHome = view === 'home';
    homeView.classList.toggle('active', toHome);
    detailView.classList.toggle('active', !toHome);
  }

  // 渲染项目列表到左侧导航
  function renderProjectsList() {
    const projectsList = qs('#projectsList');
    const projectsMenuBtn = qs('#projectsMenuBtn');
    
    if (!projectsList || !projectsMenuBtn) return;

    // 清空列表
    projectsList.innerHTML = '';

    // 渲染每个项目
    projects.forEach(project => {
      const li = document.createElement('li');
      const button = document.createElement('button');
      button.className = 'subitem';
      button.textContent = project.title;
      button.addEventListener('click', (e) => {
        e.stopPropagation();
        openDetail(project);
      });
      li.appendChild(button);
      projectsList.appendChild(li);
    });

    // 点击项目菜单按钮时切换显示
    projectsMenuBtn.addEventListener('click', () => {
      const isVisible = projectsList.style.display !== 'none';
      projectsList.style.display = isVisible ? 'none' : 'block';
      projectsMenuBtn.classList.toggle('is-active', !isVisible);
    });
  }

  // 首页分类渲染（替代旧的静态按钮）
  renderCategories();
  renderProjectsList();

  // 搜索（已移除，项目现在在左侧导航中）
  function performSearch() {
    // 搜索功能已移除，项目现在在左侧导航中显示
  }

  searchInput.addEventListener('input', performSearch);
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      performSearch();
    }
  });
  if (searchBtn) {
    searchBtn.addEventListener('click', performSearch);
  }

  // 登录功能
  const loginBtns = qsa('.login-btn');
  const roleCards = qsa('.role__card');

  loginBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      if (loginModal) loginModal.classList.add('active');
    });
  });

  if (closeModal) {
    closeModal.addEventListener('click', () => {
      if (loginModal) loginModal.classList.remove('active');
    });
  }

  if (loginModal) {
    loginModal.addEventListener('click', (e) => {
      if (e.target === loginModal || e.target.classList.contains('modal__overlay')) {
        loginModal.classList.remove('active');
      }
    });
  }

  roleCards.forEach(card => {
    card.addEventListener('click', () => {
      const role = card.dataset.role;
      handleLogin(role);
      if (loginModal) loginModal.classList.remove('active');
    });
  });

  function handleLogin(role) {
    currentUserRole = role;
    const roleNames = {
      'enterprise': '企业',
      'teacher': '高校教师',
      'user': '普通使用者'
    };

    if (currentRoleEl) {
      currentRoleEl.textContent = roleNames[role] || role;
    }

    if (featureBar) {
      featureBar.style.display = 'block';
      document.body.classList.add('has-feature-bar');
    }

    // 根据角色显示/隐藏功能按钮
    if (createProblemBtn && uploadDataBtn) {
      if (role === 'enterprise' || role === 'teacher') {
        createProblemBtn.style.display = 'inline-block';
        uploadDataBtn.style.display = 'inline-block';
      } else {
        createProblemBtn.style.display = 'none';
        uploadDataBtn.style.display = 'none';
      }
    }

    // 更新侧边栏个人中心信息
    const profileSubs = qsa('.profile__sub');
    profileSubs.forEach(el => {
      el.textContent = `已登录 · ${roleNames[role]}`;
    });
  }

  if (createProblemBtn) {
    createProblemBtn.addEventListener('click', () => {
      alert('出题功能开发中...');
    });
  }

  if (uploadDataBtn) {
    uploadDataBtn.addEventListener('click', () => {
      alert('数据上传功能开发中...');
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      currentUserRole = null;
      if (featureBar) {
        featureBar.style.display = 'none';
        document.body.classList.remove('has-feature-bar');
      }
      const profileSubs = qsa('.profile__sub');
      profileSubs.forEach(el => {
        el.textContent = '未登录 · 访客';
      });
    });
  }

  // 返回上一页（侧栏按钮）
  const backBtnSide = document.getElementById('backBtnSide');
  if (backBtnSide) {
    backBtnSide.addEventListener('click', (e) => {
      e.preventDefault();
      // 直接回首页主页面
      history.pushState({ view: 'home' }, '', '#');
      switchView('home');
      if (typeof showHomeView === 'function') showHomeView();
    });
  }

  // 轻量路由（前进后退）
  window.addEventListener('popstate', (e) => {
    if (e.state?.view === 'detail') {
      switchView('detail');
    } else {
      switchView('home');
      if (typeof showHomeView === 'function') showHomeView();
    }
  });

  // QA 区交互
  const qaTabs = qsa('.qa__tab');
  const qaMessages = document.getElementById('qaMessages');
  const qaInput = document.getElementById('qaInput');
  const qaSendBtn = document.getElementById('qaSendBtn');

  function sendQaMessage() {
    const text = (qaInput?.value || '').trim();
    if (!text) return;
    qaMessages.insertAdjacentHTML('beforeend', `<div class="msg msg--user">
      <div class="msg__avatar">你</div>
      <div class="msg__bubble">
        <div class="msg__content">${text}</div>
      </div>
    </div>`);
    qaMessages.insertAdjacentHTML('beforeend', `<div class="msg msg--ai">
      <div class="msg__avatar">AI</div>
      <div class="msg__bubble">
        <div class="msg__content">（占位）正在为你检索与生成回答…</div>
      </div>
    </div>`);
    qaMessages.scrollTop = qaMessages.scrollHeight;
    qaInput.value = '';
  }

  qaTabs.forEach(tab => tab.addEventListener('click', () => {
    qaTabs.forEach(t => t.classList.remove('is-active'));
    tab.classList.add('is-active');
    qaMessages.innerHTML = `<div class="msg msg--ai">
      <div class="msg__avatar">AI</div>
      <div class="msg__bubble">
        <div class="msg__content">已切换到 ${tab.dataset.tab === 'paper' ? '文献' : '科研'} 模式，我能为你做什么？</div>
      </div>
    </div>`;
  }));

  if (qaInput) {
    qaInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        sendQaMessage();
      }
    });
  }
  if (qaSendBtn) {
    qaSendBtn.addEventListener('click', sendQaMessage);
  }

  // 初始化
  showHomeView();
  // 恢复主题
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.body.classList.remove('theme-light');
    document.body.classList.add('theme-dark');
  }
})();


