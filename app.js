(function () {
  const qs = (s, r = document) => r.querySelector(s);
  const qsa = (s, r = document) => Array.from(r.querySelectorAll(s));

  const homeView = qs('#home-view');
  const detailView = qs('#detail-view');
  const searchInput = qs('#searchInput');
  const searchBtn = qs('#searchBtn');
  const loginModal = qs('#loginModal');
  const registerModal = qs('#registerModal');
  const closeLoginModal = qs('#closeLoginModal');
  const closeRegisterModal = qs('#closeRegisterModal');
  const loginBtn = qs('#loginBtn');
  const registerBtn = qs('#registerBtn');
  const switchToLogin = qs('#switchToLogin');
  const registerForm = qs('#registerForm');
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
  const categoryListEl = qs('#categoryList');

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
  if (projectsNavBtn) projectsNavBtn.addEventListener('click', () => {
    showProjectsView();
    toggleCategoryList();
  });
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
    const grid = document.getElementById('projectsGrid');
    if (!grid) {
      console.error('projectsGrid 元素未找到！');
      return;
    }
    
    console.log('开始渲染项目卡片，数量:', list.length);
    grid.innerHTML = '';
    
    list.forEach((p, idx) => {
      const card = document.createElement('div');
      card.className = 'card';
      card.setAttribute('data-id', p.id);
      card.style.cursor = 'pointer';
      card.innerHTML = `
        <div class="card__poster">${p.category.toUpperCase()}<span class="badge">精选</span></div>
        <div class="card__body">
          <div class="card__title">${p.title}</div>
          <div class="card__desc">${p.desc}</div>
          <div class="card__meta"><span class="thumb">👍 ${p.likes}</span></div>
        </div>
      `;
      
      // 绑定点击事件
      card.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('项目卡片被点击:', p.title, p);
        openDetail(p);
      }, false);
      
      // 额外的事件监听器确保可点击
      card.onclick = function(e) {
        console.log('onclick 事件触发:', p.title);
        openDetail(p);
      };
      
      grid.appendChild(card);
      console.log(`卡片 ${idx + 1} 已添加:`, p.title);
    });
    
    console.log('✓ 所有项目卡片渲染完成，总数:', list.length);
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
    console.log('显示项目视图');
    setPrimaryNavActive(projectsNavBtn);
    if (homeHero) homeHero.style.display = 'none';
    if (projectsView) {
      projectsView.classList.add('is-active');
      projectsView.style.display = 'block';
    }
    
    // 确保projectsGrid可见
    const grid = document.getElementById('projectsGrid');
    if (grid) {
      grid.style.display = 'grid';
      console.log('projectsGrid 设置为可见');
    }
    
    // 延迟渲染确保DOM已更新
    setTimeout(() => {
    renderCards(projects);
    }, 50);
  }

  // 切换左侧分类列表显示/隐藏
  function toggleCategoryList() {
    if (!categoryListEl) return;
    const isVisible = categoryListEl.classList.contains('is-visible');
    if (isVisible) {
      categoryListEl.classList.remove('is-visible');
      categoryListEl.style.display = 'none';
    } else {
      categoryListEl.classList.add('is-visible');
      categoryListEl.style.display = 'block';
    }
  }

  // 渲染左侧分类（可展开）
  function renderCategories() {
    if (!categoryListEl) return;
    categoryListEl.innerHTML = '';
    // "全部"
    const allLi = document.createElement('li');
    allLi.innerHTML = `<button class="nav__item is-active" data-category="all"><span class="caret">◆</span>全部</button>`;
    categoryListEl.appendChild(allLi);
    allLi.querySelector('button').addEventListener('click', () => {
      Array.from(categoryListEl.querySelectorAll('.nav__item')).forEach(b => b.classList.remove('is-active'));
      allLi.querySelector('button').classList.add('is-active');
      categoryListEl.querySelectorAll('.sublist').forEach(u => u.remove());
      renderCards(projects);
    });

    categories.forEach(cat => {
      const li = document.createElement('li');
      li.innerHTML = `<button class=\"nav__item\" data-category=\"${cat.key}\"><span class=\"caret\">▸</span>${cat.name}</button>`;
      const btn = li.querySelector('button');
      btn.addEventListener('click', () => toggleCategory(li, cat));
      categoryListEl.appendChild(li);
    });
  }

  function toggleCategory(li, cat) {
    Array.from(categoryListEl.querySelectorAll('.nav__item')).forEach(b => b.classList.remove('is-active'));
    const btn = li.querySelector('.nav__item');
    btn.classList.add('is-active');

    const opened = li.querySelector('.sublist');
    categoryListEl.querySelectorAll('.sublist').forEach(u => u.remove());
    Array.from(categoryListEl.querySelectorAll('.caret')).forEach(c => c.textContent = '▸');
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
    console.log('打开项目详情:', project);
    buildDetailMenu(project);

    const titleEl = document.getElementById('projectTitle');
    if (titleEl) titleEl.textContent = '';
    const bc = document.querySelector('.detail__breadcrumbs');
    if (bc) bc.textContent = `${project.category.toUpperCase()} · ${project.title.split('·')[0].trim()}`;

    renderDetailSection('background');
    switchView('detail');
    history.pushState({ view: 'detail', id: project.id, section: 'background' }, '', `#project/${project.id}/background`);
    
    // 重置Agent欢迎页面
    const qaWelcome = document.getElementById('qaWelcome');
    const qaChat = document.getElementById('qaChat');
    if (qaWelcome) qaWelcome.style.display = 'flex';
    if (qaChat) qaChat.style.display = 'none';
    hasGeneratedFiles = false;
    if (qaFilesBtn) qaFilesBtn.style.display = 'none';
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

  // Jupyter Notebook 单元格管理
  let notebookCells = [];
  let cellCounter = 0;

  // 简单的Markdown渲染器
  function renderMarkdown(markdown) {
    let html = markdown;
    
    // 标题转换
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    
    // 处理列表（转换为数字列表）
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, match => `<ol>${match}</ol>`);
    
    // 段落
    const lines = html.split('\n');
    let result = [];
    let inList = false;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.startsWith('<h') || line.startsWith('<ol') || line.startsWith('</ol') || line.startsWith('<li')) {
        result.push(line);
        inList = line.startsWith('<ol') || (inList && !line.startsWith('</ol'));
      } else if (line) {
        if (!inList && !lines[i-1]?.trim().startsWith('<h')) {
          result.push(`<p>${line}</p>`);
        } else {
          result.push(line);
        }
      }
    }
    
    return result.join('\n');
  }

  function createNotebookCell(type = 'code', content = '', language = 'python') {
    const cellId = `cell-${cellCounter++}`;
    const cell = {
      id: cellId,
      type: type,
      content: content,
      language: language,
      output: null
    };
    notebookCells.push(cell);
    return cell;
  }

  function renderNotebookCell(cell, index) {
    const cellDiv = document.createElement('div');
    cellDiv.className = `notebook-cell ${cell.type}-cell`;
    cellDiv.dataset.cellId = cell.id;
    
    // 添加编号（代码块和表格）
    if (cell.type === 'code' || cell.type === 'table') {
      const cellNumber = document.createElement('div');
      cellNumber.className = 'cell-number';
      cellNumber.textContent = `[${index + 1}]:`;
      cellDiv.appendChild(cellNumber);
    }
    
    if (cell.type === 'table') {
      // 渲染表格（图示）
      const tableData = cell.content;
      let tableHTML = `<div class="table-container">`;
      
      if (tableData.title) {
        tableHTML += `<p style="margin-bottom: 16px;">${tableData.title}</p>`;
      }
      
      tableHTML += `<div class="conv-diagram">
        <div class="diagram-row">
          <div class="diagram-label">输入</div>
          <div class="diagram-values">
            ${tableData.data.input.map((v, i) => `<div class="value-cell ${i < 2 ? 'highlight' : ''}">${v}</div>`).join('')}
          </div>
          </div>
        <div class="diagram-row">
          <div class="diagram-label">核</div>
          <div class="diagram-values diagram-kernel">
            <span class="operator">*</span>
            ${Array.isArray(tableData.data.kernel[0]) 
              ? tableData.data.kernel.map(row => 
                  `<div class="kernel-row">${row.map(v => `<div class="value-cell highlight">${v}</div>`).join('')}</div>`
                ).join('')
              : tableData.data.kernel.map(v => `<div class="value-cell highlight">${v}</div>`).join('')
            }
          </div>
        </div>
        <div class="diagram-row">
          <div class="diagram-label">输出</div>
          <div class="diagram-values">
            <span class="operator">=</span>
            ${tableData.data.output.map(v => `<div class="value-cell">${v}</div>`).join('')}
          </div>
        </div>
        <div class="diagram-label-ref">:label: ${tableData.data.label}</div>
      </div>`;
      tableHTML += `</div>`;
      
      cellDiv.innerHTML += tableHTML;
    } else if (cell.type === 'code') {
      const cellWrapper = document.createElement('div');
      cellWrapper.className = 'cell-wrapper';
      
      cellWrapper.innerHTML = `
        <div class="cell-toolbar">
          <button class="toolbar-btn run-cell" title="运行代码">
            <svg viewBox="0 0 24 24" fill="none"><path d="M8 5v14l11-7z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <button class="toolbar-btn move-up" title="上移">
            <svg viewBox="0 0 24 24" fill="none"><path d="M18 15l-6-6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <button class="toolbar-btn move-down" title="下移">
            <svg viewBox="0 0 24 24" fill="none"><path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <button class="toolbar-btn add-above" title="在上方添加">
            <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 8v8M8 12h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </button>
          <button class="toolbar-btn add-below" title="在下方添加">
            <svg viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/><path d="M12 8v8M8 12h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </button>
          <button class="toolbar-btn delete-cell" title="删除">
            <svg viewBox="0 0 24 24" fill="none"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <div class="cell-content">
          <textarea class="cell-input" placeholder="在此输入代码...">${cell.content}</textarea>
          ${cell.output ? `<div class="cell-output">${cell.output}</div>` : ''}
        </div>
      `;
      
      cellDiv.appendChild(cellWrapper);
    } else {
      // Markdown单元格 - 渲染为HTML，可编辑
      const renderedContent = renderMarkdown(cell.content);
      const cellWrapper = document.createElement('div');
      cellWrapper.className = 'cell-wrapper';
      
      cellWrapper.innerHTML = `
        <div class="cell-toolbar">
          <button class="toolbar-btn move-up" title="上移">
            <svg viewBox="0 0 24 24" fill="none"><path d="M18 15l-6-6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <button class="toolbar-btn move-down" title="下移">
            <svg viewBox="0 0 24 24" fill="none"><path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <button class="toolbar-btn add-above" title="在上方添加">
            <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 8v8M8 12h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </button>
          <button class="toolbar-btn add-below" title="在下方添加">
            <svg viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/><path d="M12 8v8M8 12h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </button>
          <button class="toolbar-btn delete-cell" title="删除">
            <svg viewBox="0 0 24 24" fill="none"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
        <div class="cell-content">
          <textarea class="cell-input" style="display: none;">${cell.content}</textarea>
        </div>
      `;
      
      cellDiv.appendChild(cellWrapper);
      
      // 添加渲染的Markdown内容
      const mdRendered = document.createElement('div');
      mdRendered.className = 'markdown-rendered';
      mdRendered.innerHTML = renderedContent;
      cellDiv.querySelector('.cell-content').appendChild(mdRendered);
      
      // 点击Markdown进入编辑模式
      mdRendered.addEventListener('click', () => {
        enterMarkdownEditMode(cellDiv, cell);
      });
    }

    // 绑定代码块事件
    const textarea = cellDiv.querySelector('.cell-input');
    
    if (textarea && cell.type === 'code') {
      // 自动调整textarea高度
      const autoResize = () => {
        textarea.style.height = 'auto';
        textarea.style.height = Math.max(100, textarea.scrollHeight) + 'px';
      };
      
    textarea.addEventListener('input', (e) => {
      cell.content = e.target.value;
        autoResize();
      });
      
      // 失去焦点时退出Markdown编辑模式
      textarea.addEventListener('blur', () => {
        if (cell.type === 'markdown') {
          exitMarkdownEditMode(cellDiv, cell);
        }
      });
      
      // 初始化时调整高度
      setTimeout(autoResize, 0);
      
      // 点击选中
      cellDiv.addEventListener('click', () => {
        document.querySelectorAll('.notebook-cell').forEach(c => c.classList.remove('active'));
        cellDiv.classList.add('active');
      });
    }

    // 工具栏按钮事件
    const runBtn = cellDiv.querySelector('.run-cell');
    if (runBtn) {
      runBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        runCell(cell, cellDiv);
      });
    }

    const moveUpBtn = cellDiv.querySelector('.move-up');
    if (moveUpBtn) {
      moveUpBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        moveCellUp(cell.id);
      });
    }

    const moveDownBtn = cellDiv.querySelector('.move-down');
    if (moveDownBtn) {
      moveDownBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        moveCellDown(cell.id);
      });
    }

    const addAboveBtn = cellDiv.querySelector('.add-above');
    if (addAboveBtn) {
      addAboveBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        addCellAbove(cell.id);
      });
    }

    const addBelowBtn = cellDiv.querySelector('.add-below');
    if (addBelowBtn) {
      addBelowBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        addCellBelow(cell.id);
      });
    }

    const deleteBtn = cellDiv.querySelector('.delete-cell');
    if (deleteBtn) {
      deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
      notebookCells = notebookCells.filter(c => c.id !== cell.id);
        rerenderNotebook();
    });
    }

    return cellDiv;
  }

  // Markdown编辑模式切换
  function enterMarkdownEditMode(cellDiv, cell) {
    cellDiv.classList.add('editing');
    cellDiv.classList.add('active');
    const textarea = cellDiv.querySelector('.cell-input');
    const mdRendered = cellDiv.querySelector('.markdown-rendered');
    
    if (textarea) {
      textarea.style.display = 'block';
      textarea.value = cell.content;
      textarea.focus();
      
      // 自动调整高度
      textarea.style.height = 'auto';
      textarea.style.height = Math.max(100, textarea.scrollHeight) + 'px';
      
      // 输入时更新
      textarea.oninput = (e) => {
        cell.content = e.target.value;
        textarea.style.height = 'auto';
        textarea.style.height = Math.max(100, textarea.scrollHeight) + 'px';
      };
      
      // 失去焦点时退出编辑模式
      textarea.onblur = () => {
        setTimeout(() => exitMarkdownEditMode(cellDiv, cell), 200);
      };
    }
  }

  function exitMarkdownEditMode(cellDiv, cell) {
    cellDiv.classList.remove('editing');
    const mdRendered = cellDiv.querySelector('.markdown-rendered');
    if (mdRendered) {
      mdRendered.innerHTML = renderMarkdown(cell.content);
    }
  }

  // 辅助函数
  function moveCellUp(cellId) {
    const idx = notebookCells.findIndex(c => c.id === cellId);
    if (idx > 0) {
      [notebookCells[idx - 1], notebookCells[idx]] = [notebookCells[idx], notebookCells[idx - 1]];
      rerenderNotebook();
    }
  }

  function moveCellDown(cellId) {
    const idx = notebookCells.findIndex(c => c.id === cellId);
    if (idx < notebookCells.length - 1) {
      [notebookCells[idx], notebookCells[idx + 1]] = [notebookCells[idx + 1], notebookCells[idx]];
      rerenderNotebook();
    }
  }

  function addCellAbove(cellId) {
    const idx = notebookCells.findIndex(c => c.id === cellId);
    const newCell = createNotebookCell('code', '', 'python');
    notebookCells.splice(idx, 0, newCell);
    rerenderNotebook();
  }

  function addCellBelow(cellId) {
    const idx = notebookCells.findIndex(c => c.id === cellId);
    const newCell = createNotebookCell('code', '', 'python');
    notebookCells.splice(idx + 1, 0, newCell);
    rerenderNotebook();
  }

  function rerenderNotebook() {
    const container = document.querySelector('.notebook-container');
    if (!container) return;
    
    const cellsContainer = container.querySelector('.cells-wrapper') || container;
    const cells = cellsContainer.querySelectorAll('.notebook-cell');
    cells.forEach(c => c.remove());
    
    notebookCells.forEach((cell, index) => {
      const cellDiv = renderNotebookCell(cell, index);
      const addBtn = cellsContainer.querySelector('.add-cell-btn');
      if (addBtn) {
        cellsContainer.insertBefore(cellDiv, addBtn);
      } else {
        cellsContainer.appendChild(cellDiv);
      }
    });
  }

  // Python执行环境（状态保持）
  const pythonEnv = {
    variables: {},
    functions: {}
  };

  function runCell(cell, cellDiv) {
    // 执行单元格内的所有代码
    const code = cell.content.trim();
    let output = '';
    
    try {
      if (cell.language === 'python') {
        // 实际执行Python代码的模拟（带状态保持）
        
        // 保存函数定义
        if (code.includes('def corr1d')) {
          pythonEnv.functions.corr1d = function(X, K) {
            const w = K.length;
            const Y = [];
            for (let i = 0; i <= X.length - w; i++) {
              let sum = 0;
              for (let j = 0; j < w; j++) {
                sum += X[i + j] * K[j];
              }
              Y.push(sum);
            }
            return Y;
          };
          output = ''; // 函数定义无输出
        }
        // 执行corr1d(X, K)
        else if (code.includes('corr1d(X, K)') && pythonEnv.functions.corr1d) {
          const X = pythonEnv.variables.X || [0, 1, 2, 3, 4, 5, 6];
          const K = pythonEnv.variables.K || [1, 2];
          const result = pythonEnv.functions.corr1d(X, K);
          output = `tensor([${result.map(v => `${v.toFixed(0)}.`).join(', ')}])`;
        }
        // 变量赋值
        else if (code.includes('X, K = torch.tensor')) {
          pythonEnv.variables.X = [0, 1, 2, 3, 4, 5, 6];
          pythonEnv.variables.K = [1, 2];
          output = ''; // 赋值无输出
        }
        // 处理print语句
        else if (code.includes('print(')) {
          const printRegex = /print\((.+?)\)/g;
          const outputs = [];
          let match;
          while ((match = printRegex.exec(code)) !== null) {
            try {
              let printContent = match[1];
              if (printContent.includes('f"') || printContent.includes("f'")) {
                printContent = printContent
                  .replace(/f["'](.+?)["']/g, '$1')
                  .replace(/\{(.+?)\}/g, (_, expr) => {
                    if (expr.includes('.shape')) return '[形状]';
                    return '{值}';
                  });
              }
              printContent = printContent.replace(/["']/g, '');
              outputs.push(printContent);
            } catch (e) {
              outputs.push(match[1]);
            }
          }
          output = outputs.join('\n');
        }
        // 其他代码
        else if (code.includes('def ') || code.includes('class ')) {
          output = '';
        } else if (code.includes('=') && !code.includes('print')) {
          output = '';
        } else {
          output = '';
        }
      } else if (cell.language === 'javascript') {
        output = eval(code);
      } else {
        output = '';
      }
    } catch (e) {
      output = `错误: ${e.message}`;
    }

    cell.output = output;
    
    // 更新或创建输出区域
    const cellContent = cellDiv.querySelector('.cell-content');
    if (cellContent) {
      let outputDiv = cellContent.querySelector('.cell-output');
      
      if (output) {
    if (!outputDiv) {
      outputDiv = document.createElement('div');
      outputDiv.className = 'cell-output';
          cellContent.appendChild(outputDiv);
    }
    outputDiv.textContent = output;
    
    if (output.startsWith('错误:')) {
      outputDiv.classList.add('error');
    } else {
      outputDiv.classList.remove('error');
        }
      } else if (outputDiv) {
        outputDiv.remove();
      }
    }
  }

  function renderNotebook(containerId, initialCells = []) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '';
    const notebookDiv = document.createElement('div');
    notebookDiv.className = 'notebook-container';

    // 渲染初始单元格
    if (initialCells.length === 0) {
      initialCells = [
        { type: 'markdown', content: '# 项目笔记\n\n在这里记录你的想法和代码实验...' },
        { type: 'code', content: '# 在此编写代码\nprint("Hello, World!")', language: 'python' }
      ];
    }

    notebookCells = [];
    cellCounter = 0;

    initialCells.forEach((cellData, index) => {
      if (cellData.type === 'hidden') {
        // 渲染隐藏单元格提示
        const hiddenHint = document.createElement('div');
        hiddenHint.className = 'hidden-cells-hint';
        hiddenHint.textContent = `+ ${cellData.count} cells hidden`;
        hiddenHint.addEventListener('click', () => {
          // 展开隐藏的单元格
          hiddenHint.remove();
          let currentIndex = notebookCells.length;
          cellData.cells.forEach((hiddenCellData, i) => {
            const cell = createNotebookCell(hiddenCellData.type, hiddenCellData.content, hiddenCellData.language || 'python');
            const cellDiv = renderNotebookCell(cell, currentIndex + i);
            const addBtn = notebookDiv.querySelector('.add-cell-btn');
            if (addBtn) {
              notebookDiv.insertBefore(cellDiv, addBtn);
            } else {
              notebookDiv.appendChild(cellDiv);
            }
          });
        });
        notebookDiv.appendChild(hiddenHint);
      } else {
      const cell = createNotebookCell(cellData.type, cellData.content, cellData.language || 'python');
        const cellDiv = renderNotebookCell(cell, index);
      notebookDiv.appendChild(cellDiv);
      }
    });

    // 添加"添加单元格"按钮
    const addCellBtn = document.createElement('button');
    addCellBtn.className = 'add-cell-btn';
    addCellBtn.textContent = '+ 添加代码单元格';
    addCellBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const newCell = createNotebookCell('code', '', 'python');
      rerenderNotebook();
    }, { once: false });

    notebookDiv.appendChild(addCellBtn);
    container.appendChild(notebookDiv);
  }

  function renderDetailSection(key) {
    const wrap = document.getElementById('detailContent');
    const videoArea = document.querySelector('.detail__video');
    
    // 个性化检验和留言区：隐藏视频区域
    if (key === 'personalize' || key === 'comments') {
      if (videoArea) videoArea.style.display = 'none';
    } else {
      if (videoArea) videoArea.style.display = '';
    }
    
    // 使用Notebook的部分
    if (key === 'background' || key === 'model' || key === 'model-intro' || key === 'baseline' || key === 'idea') {
      const notebookData = {
        'background': [
          { type: 'markdown', content: '# 背景\n\n在真实相机成像链路中，噪声来源包括读出噪声、光子噪声以及 ISP 处理引入的复合噪声。低照度、运动模糊与复杂背景进一步放大噪声影响，导致细节丢失与纹理伪影。' },
          { type: 'markdown', content: '## 数据来源\n\n- 合成数据集（DND、SIDD）\n- 真实数据集（自采样室内外场景）\n- 混合训练策略' },
          { type: 'code', content: '# 数据加载示例\nimport torch\nfrom torch.utils.data import Dataset\nimport numpy as np\nfrom PIL import Image\n\nprint("初始化数据加载器...")\nprint("DND数据集: 50张图像")\nprint("SIDD数据集: 320对图像")', language: 'python' },
          { type: 'markdown', content: '## 任务目标\n\n- 在保持结构一致性的前提下提升 PSNR/SSIM\n- 兼顾 LPIPS 感知质量\n- 实时推理速度 < 50ms' },
          { type: 'markdown', content: '## 难点分析\n\n- 弱光噪声分布不均\n- 跨设备域泛化能力\n- 速度与质量的平衡' },
          { type: 'hidden', count: 5, cells: [
            { type: 'code', content: '# 数据预处理管道\nfrom torchvision import transforms\n\ntransform = transforms.Compose([\n    transforms.RandomCrop(256),\n    transforms.RandomHorizontalFlip(),\n    transforms.ToTensor()\n])\n\nprint("数据增强管道已创建")', language: 'python' },
            { type: 'markdown', content: '数据增强对于提升模型泛化能力至关重要。我们采用随机裁剪、翻转等增强方式。' },
            { type: 'code', content: '# 创建数据加载器\ndataloader = torch.utils.data.DataLoader(\n    dataset,\n    batch_size=16,\n    shuffle=True,\n    num_workers=4\n)\n\nprint(f"数据加载器已创建，批次大小: 16")', language: 'python' },
            { type: 'markdown', content: '使用多线程数据加载可以显著提升训练效率。' },
            { type: 'code', content: '# 验证数据形状\nfor noisy, clean in dataloader:\n    print(f"Noisy shape: {noisy.shape}")\n    print(f"Clean shape: {clean.shape}")\n    break', language: 'python' }
          ]}
        ],
        'model': [
          { type: 'markdown', content: '# 模型架构\n\n采用多尺度 U-Net 主干，结合噪声估计支路与频域残差补偿。整体结构为 Encoder-Decoder 框架，带跨层跳连与注意力模块。' },
          { type: 'code', content: '# 模型定义\nimport torch.nn as nn\n\nclass DenoiseModel(nn.Module):\n    def __init__(self, in_channels=3, base_dim=64):\n        super().__init__()\n        self.encoder = nn.Conv2d(in_channels, base_dim, 3, padding=1)\n        self.decoder = nn.Conv2d(base_dim, in_channels, 3, padding=1)', language: 'python' },
          { type: 'markdown', content: '## 核心模块\n\n模型包含以下关键组件：\n\n- 自适应门控注意力（AGA）模块\n- 频域残差增强（FRE）模块\n- 多尺度特征融合' },
          { type: 'code', content: '    def forward(self, x):\n        features = self.encoder(x)\n        output = self.decoder(features)\n        return output + x  # 残差连接\n\nmodel = DenoiseModel()\nprint(f"模型参数量: {sum(p.numel() for p in model.parameters())/1e6:.2f}M")', language: 'python' },
          { type: 'markdown', content: '训练阶段引入合成+真实的混合噪声建模与自蒸馏策略。' }
        ],
        'model-intro': [
          { type: 'markdown', content: '# 一维卷积\n\n在介绍该模型之前，让我们先看看一维卷积是如何工作的。请记住，这只是基于互相关运算的二维卷积的特例。' },
          { type: 'table', content: {
            title: '下面展示了输入、核和输出的关系：',
            data: {
              input: [0, 1, 2, 3, 4, 5, 6],
              kernel: [1, 2],
              output: [2, 5, 8, 11, 14, 17],
              label: 'fig_conv1d'
            }
          }},
          { type: 'markdown', content: '如 :numref:`fig_conv1d` 中所示，在一维情况下，卷积窗口在输入张量上从左向右滑动。在滑动期间，卷积窗口中某个位置包含的输入子张量（例如，:numref:`fig_conv1d` 中的0和1）和核张量（例如，:numref:`fig_conv1d` 中的1和2）按元素相乘。这些乘法的总和在输出张量的相应位置给出单个标量值（例如，:numref:`fig_conv1d` 中的 0 × 1 + 1 × 2 = 2）。' },
          { type: 'markdown', content: '我们在下面的 corrid 函数中实现了一维互相关。给定输入张量 X 和核张量 K，它返回输出张量 Y。' },
          { type: 'code', content: 'def corr1d(X, K):\n    w = K.shape[0]\n    Y = torch.zeros((X.shape[0] - w + 1))\n    for i in range(Y.shape[0]):\n        Y[i] = (X[i: i + w] * K).sum()\n    return Y', language: 'python' },
          { type: 'markdown', content: '我们可以从 :numref:`fig_conv1d` 中构造输入张量X和核张量K来验证上述一维卷积的实现。' },
          { type: 'code', content: 'X, K = torch.tensor([0, 1, 2, 3, 4, 5, 6]), torch.tensor([1, 2])\ncorr1d(X, K)', language: 'python' },
          { type: 'markdown', content: '对于任何具有多个通道的一维输入，卷积核需要具有相同数量的输入通道。然后，对于每个通道，对输入的一维张量和卷积核的一维张量进行互相关运算，将所有通道上的结果相加以产生一维输出张量。:numref:`fig_conv1d_channel` 演示了具有3个输入通道的一维互相关运算。' },
          { type: 'hidden', count: 5, cells: [
            { type: 'markdown', content: '注意，多输入通道的一维互相关等同于单输入通道的二维互相关。举例说明，:numref:`fig_conv1d_channel` 中的多输入通道一维互相关的等价形式是 :numref:`fig_conv1d_2d` 中的单输入通道二维互相关，其中卷积核的高度必须与输入张量的高度相同。' },
            { type: 'table', content: {
              title: '多通道一维卷积示意：',
              data: {
                input: [[2,3,4,5,6,7,8], [1,2,3,4,5,6,7], [0,1,2,3,4,5,6]],
                kernel: [[-1,-3], [3,4], [1,2]],
                output: [2, 8, 14, 20, 26, 32],
                label: 'fig_conv1d_2d'
              }
            }},
            { type: 'markdown', content: ':numref:`fig_conv1d` 和 :numref:`fig_conv1d_channel` 中的输出都只有一个通道。与 :numref:`subsec_multi-output-channels` 中描述的具有多个输出通道的二维卷积相同，我们也可以为一维卷积指定多个输出通道。' },
            { type: 'markdown', content: '## 最大时间汇聚层\n\n类似地，我们可以使用汇聚层从序列表示中提取最大值，作为跨时间步的最重要特征。textCNN中使用的最大时间汇聚层的工作原理类似于一维全局汇聚 :cite:`Collobert.Weston.Bottou.ea.2011` 。对于每个通道在不同时间步存储值的多通道输入，每个通道的输出是该通道的最大值。请注意，最大时间汇聚允许在不同通道上使用不同数量的时间步。' }
          ]}
        ],
        'baseline': [
          { type: 'markdown', content: '# Baseline介绍\n\n对比 BM3D、DnCNN、RIDNet、NAFNet 等。' }
        ],
        'idea': [
          { type: 'markdown', content: '# IDEA引导\n\n本项目提供以下优化方向供探索。' },
          { type: 'markdown', content: '## 数据增强策略\n\n- 合成噪声混入相机 ISP 模拟过程\n- 多尺度裁剪与旋转增强\n- 混合噪声级别训练' },
          { type: 'code', content: '# 数据增强实现\nimport numpy as np\n\ndef add_realistic_noise(img, noise_level=0.1):\n    # 泊松噪声（光子噪声）\n    shot = np.random.poisson(img * 255) / 255.0\n    # 高斯噪声（读出噪声）\n    read = np.random.normal(0, noise_level, img.shape)\n    return np.clip(shot + read, 0, 1)', language: 'python' },
          { type: 'markdown', content: '## 结构优化方向\n\n- 探索轻量 Transformer 模块\n- 频域-空域双分支设计\n- 渐进式降噪策略' },
          { type: 'code', content: '# 实验代码区\n# 在此尝试你的创新想法\n\nimport torch\n\n# 测试数据增强\ntest_img = torch.rand(1, 3, 256, 256)\nnoisy = add_realistic_noise(test_img.numpy())\nprint(f"原始图像: {test_img.shape}, 噪声图像: {noisy.shape}")', language: 'python' }
        ]
      };

      // 旧的HTML内容数据（暂时保留注释）
      const oldContentData = {
        'background': `
<div class="content-section">
  <h2>背景</h2>
  <p>在真实相机成像链路中，噪声来源包括读出噪声、光子噪声以及 ISP 处理引入的复合噪声。低照度、运动模糊与复杂背景进一步放大噪声影响，导致细节丢失与纹理伪影。</p>
  
  <h3>数据来源</h3>
  <p>合成+真实数据集（DND、SIDD、自采样室内外场景）。</p>
  
  <h3>任务目标</h3>
  <p>在保持结构一致性的前提下提升 PSNR/SSIM，并兼顾 LPIPS 感知质量。</p>
  
  <h3>难点</h3>
  <ul>
    <li>弱光噪声分布不均</li>
    <li>跨设备域泛化</li>
    <li>速度与质量的平衡</li>
  </ul>
  
  <div class="code-block">
    <div class="code-header">Python</div>
    <pre><code># 数据加载示例
import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
from PIL import Image

class DenoiseDataset(Dataset):
    def __init__(self, noisy_dir, clean_dir, transform=None):
        self.noisy_images = sorted(glob.glob(f"{noisy_dir}/*.png"))
        self.clean_images = sorted(glob.glob(f"{clean_dir}/*.png"))
        self.transform = transform
    
    def __len__(self):
        return len(self.noisy_images)
    
    def __getitem__(self, idx):
        noisy = Image.open(self.noisy_images[idx]).convert('RGB')
        clean = Image.open(self.clean_images[idx]).convert('RGB')
        
        if self.transform:
            noisy = self.transform(noisy)
            clean = self.transform(clean)
        
        return noisy, clean

# 加载DND数据集
dataset = DenoiseDataset('data/noisy', 'data/clean')
dataloader = DataLoader(dataset, batch_size=8, shuffle=True)</code></pre>
  </div>
</div>`,
        'model': `
<div class="content-section">
  <h2>模型架构</h2>
  <p>采用多尺度 U-Net 主干，结合噪声估计支路与频域残差补偿；训练阶段引入合成+真实的混合噪声建模与自蒸馏策略。</p>
  
  <h3>整体结构</h3>
  <p>Encoder-Decoder 框架，带跨层跳连与注意力模块。</p>
  
  <div class="code-block">
    <div class="code-header">Python</div>
    <pre><code>import torch
import torch.nn as nn

class DenoiseModel(nn.Module):
    def __init__(self, in_channels=3, out_channels=3, base_dim=64):
        super(DenoiseModel, self).__init__()
        
        # Encoder
        self.enc1 = nn.Sequential(
            nn.Conv2d(in_channels, base_dim, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(base_dim, base_dim, 3, padding=1),
            nn.ReLU(inplace=True)
        )
        self.pool1 = nn.MaxPool2d(2, 2)
        
        self.enc2 = nn.Sequential(
            nn.Conv2d(base_dim, base_dim*2, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(base_dim*2, base_dim*2, 3, padding=1),
            nn.ReLU(inplace=True)
        )
        self.pool2 = nn.MaxPool2d(2, 2)
        
        # Bottleneck with attention
        self.bottleneck = nn.Sequential(
            nn.Conv2d(base_dim*2, base_dim*4, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(base_dim*4, base_dim*4, 3, padding=1),
            nn.ReLU(inplace=True)
        )
        
        # Decoder
        self.up1 = nn.ConvTranspose2d(base_dim*4, base_dim*2, 2, stride=2)
        self.dec1 = nn.Sequential(
            nn.Conv2d(base_dim*4, base_dim*2, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(base_dim*2, base_dim*2, 3, padding=1),
            nn.ReLU(inplace=True)
        )
        
        self.up2 = nn.ConvTranspose2d(base_dim*2, base_dim, 2, stride=2)
        self.dec2 = nn.Sequential(
            nn.Conv2d(base_dim*2, base_dim, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(base_dim, base_dim, 3, padding=1),
            nn.ReLU(inplace=True)
        )
        
        self.out_conv = nn.Conv2d(base_dim, out_channels, 1)
    
    def forward(self, x):
        # Encoder
        enc1 = self.enc1(x)
        enc1_pool = self.pool1(enc1)
        
        enc2 = self.enc2(enc1_pool)
        enc2_pool = self.pool2(enc2)
        
        # Bottleneck
        bottleneck = self.bottleneck(enc2_pool)
        
        # Decoder with skip connections
        dec1 = self.up1(bottleneck)
        dec1 = torch.cat([dec1, enc2], dim=1)
        dec1 = self.dec1(dec1)
        
        dec2 = self.up2(dec1)
        dec2 = torch.cat([dec2, enc1], dim=1)
        dec2 = self.dec2(dec2)
        
        out = self.out_conv(dec2)
        return out + x  # 残差连接

model = DenoiseModel()
print(f"模型参数量: {sum(p.numel() for p in model.parameters())/1e6:.2f}M")</code></pre>
  </div>
</div>`,
        'model-intro': `
<div class="content-section">
  <h2>模型介绍</h2>
  <p>包含自适应门控注意力（AGA）模块与频域残差增强（FRE）模块。</p>
  
  <h3>主要特点</h3>
  <ul>
    <li>多尺度特征提取</li>
    <li>自适应噪声估计</li>
    <li>频域信息补偿</li>
    <li>端到端训练</li>
  </ul>
</div>`,
        'baseline': `
<div class="content-section">
  <h2>Baseline介绍</h2>
  <p>对比 BM3D、DnCNN、RIDNet、NAFNet 等经典与SOTA方法。</p>
  
  <h3>对比方法</h3>
  <table class="comparison-table">
    <thead>
      <tr>
        <th>方法</th>
        <th>PSNR (dB)</th>
        <th>SSIM</th>
        <th>参数量 (M)</th>
        <th>速度 (ms)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>BM3D</td>
        <td>32.5</td>
        <td>0.875</td>
        <td>-</td>
        <td>2500</td>
      </tr>
      <tr>
        <td>DnCNN</td>
        <td>34.2</td>
        <td>0.912</td>
        <td>0.56</td>
        <td>15</td>
      </tr>
      <tr>
        <td>RIDNet</td>
        <td>36.8</td>
        <td>0.945</td>
        <td>1.5</td>
        <td>25</td>
      </tr>
      <tr>
        <td>NAFNet</td>
        <td>38.1</td>
        <td>0.958</td>
        <td>2.1</td>
        <td>32</td>
      </tr>
      <tr style="background: rgba(160, 82, 45, 0.1);">
        <td><strong>本方法</strong></td>
        <td><strong>39.3</strong></td>
        <td><strong>0.965</strong></td>
        <td><strong>1.8</strong></td>
        <td><strong>28</strong></td>
      </tr>
    </tbody>
  </table>
</div>`,
        'idea': `
<div class="content-section">
  <h2>IDEA引导</h2>
  
  <h3>数据增强方向</h3>
  <ul>
    <li>合成噪声混入相机 ISP 模拟过程</li>
    <li>真实噪声采样与迁移</li>
    <li>动态场景噪声建模</li>
  </ul>
  
  <h3>结构优化方向</h3>
  <ul>
    <li>探索轻量 Transformer 模块</li>
    <li>频域信息融合</li>
    <li>自适应噪声估计网络</li>
    <li>多尺度特征融合策略</li>
  </ul>
  
  <h3>训练策略</h3>
  <ul>
    <li>多阶段训练：先合成数据，后真实数据微调</li>
    <li>混合损失函数：L1 + 感知损失 + 对抗损失</li>
    <li>知识蒸馏：大模型指导小模型</li>
  </ul>
  
  <div class="code-block">
    <div class="code-header">实验代码区</div>
    <pre><code># 在此尝试你的想法
import torch
import torch.nn as nn

# 示例：添加注意力模块
class AttentionBlock(nn.Module):
    def __init__(self, channels):
        super(AttentionBlock, self).__init__()
        self.query = nn.Conv2d(channels, channels//8, 1)
        self.key = nn.Conv2d(channels, channels//8, 1)
        self.value = nn.Conv2d(channels, channels, 1)
        self.gamma = nn.Parameter(torch.zeros(1))
    
    def forward(self, x):
        B, C, H, W = x.size()
        
        query = self.query(x).view(B, -1, H*W).permute(0, 2, 1)
        key = self.key(x).view(B, -1, H*W)
        energy = torch.bmm(query, key)
        attention = torch.softmax(energy, dim=-1)
        
        value = self.value(x).view(B, -1, H*W)
        out = torch.bmm(value, attention.permute(0, 2, 1))
        out = out.view(B, C, H, W)
        
        return self.gamma * out + x

# 测试
attention = AttentionBlock(64)
x = torch.randn(1, 64, 32, 32)
out = attention(x)
print(f"输入: {x.shape}, 输出: {out.shape}")</code></pre>
  </div>
</div>`
      };
      
      wrap.innerHTML = '';
      renderNotebook('detailContent', notebookData[key] || []);
    } else if (key === 'personalize') {
      renderPersonalizeSection(wrap);
    } else if (key === 'comments') {
      renderCommentsSection(wrap);
    } else {
      wrap.innerHTML = `<p>即将上线…</p>`;
    }
  }

  function renderPersonalizeSection(wrap) {
    // 个性化检验 - 10道选择题
    const quizData = [
      {
        question: "在图像去噪任务中，PSNR指标主要衡量什么？",
        options: ["图像的感知质量", "图像的峰值信噪比", "图像的结构相似度", "图像的颜色准确度"],
        correct: 1
      },
      {
        question: "ISP（Image Signal Processor）主要用于？",
        options: ["深度学习模型训练", "相机原始信号处理", "图像压缩", "视频编码"],
        correct: 1
      },
      {
        question: "DND数据集主要用于哪种任务？",
        options: ["图像分类", "图像去噪", "目标检测", "语义分割"],
        correct: 1
      },
      {
        question: "在深度学习中，Encoder-Decoder架构主要用于？",
        options: ["分类任务", "回归任务", "序列到序列任务", "聚类任务"],
        correct: 2
      },
      {
        question: "LPIPS指标主要衡量什么？",
        options: ["图像的峰值信噪比", "图像的感知相似度", "图像的结构相似度", "图像的均方误差"],
        correct: 1
      },
      {
        question: "在图像处理中，跨层跳连（Skip Connection）的主要作用是？",
        options: ["减少参数量", "保留细节信息", "加速训练", "防止过拟合"],
        correct: 1
      },
      {
        question: "注意力机制（Attention Mechanism）的核心思想是？",
        options: ["增加模型深度", "选择性关注重要特征", "减少计算量", "增加参数量"],
        correct: 1
      },
      {
        question: "Baseline模型的作用是？",
        options: ["作为最终模型", "作为对比参考", "作为数据预处理", "作为损失函数"],
        correct: 1
      },
      {
        question: "在真实相机成像中，噪声的主要来源不包括？",
        options: ["读出噪声", "光子噪声", "ISP处理噪声", "显示器噪声"],
        correct: 3
      },
      {
        question: "SSIM（Structural Similarity Index）主要关注图像的什么特性？",
        options: ["颜色准确度", "结构相似性", "亮度均匀度", "边缘锐利度"],
        correct: 1
      }
    ];

    let userAnswers = new Array(quizData.length).fill(null);
    let submitted = false;

    const quizHTML = `
      <div class="quiz-container">
        <div class="quiz-header">
          <h2 class="quiz-title">个性化检验</h2>
          <p class="quiz-desc">测试你对本项目相关知识的理解程度</p>
        </div>
        ${quizData.map((q, idx) => `
          <div class="quiz-question" data-question="${idx}">
            <div class="question-number">第 ${idx + 1} 题</div>
            <div class="question-text">${q.question}</div>
            <div class="quiz-options">
              ${q.options.map((opt, optIdx) => `
                <div class="quiz-option" data-question="${idx}" data-option="${optIdx}">
                  <div class="option-label">${String.fromCharCode(65 + optIdx)}</div>
                  <div class="option-text">${opt}</div>
                </div>
              `).join('')}
            </div>
          </div>
        `).join('')}
        <div class="quiz-actions">
          <button class="btn btn--primary btn--large" id="submitQuiz">提交答案</button>
          <button class="btn btn--ghost btn--large" id="resetQuiz">重新开始</button>
        </div>
        <div id="quizResult" style="display: none;"></div>
      </div>
    `;

    wrap.innerHTML = quizHTML;

    // 绑定选项点击事件
    const options = wrap.querySelectorAll('.quiz-option');
    options.forEach(opt => {
      opt.addEventListener('click', () => {
        if (submitted) return;
        
        const questionIdx = parseInt(opt.dataset.question);
        const optionIdx = parseInt(opt.dataset.option);
        
        // 取消同一题的其他选项
        const sameQuestion = wrap.querySelectorAll(`[data-question="${questionIdx}"]`);
        sameQuestion.forEach(o => o.classList.remove('selected'));
        
        // 选中当前选项
        opt.classList.add('selected');
        userAnswers[questionIdx] = optionIdx;
      });
    });

    // 提交答案
    const submitBtn = wrap.querySelector('#submitQuiz');
    submitBtn.addEventListener('click', () => {
      if (submitted) return;
      
      // 检查是否所有题目都已作答
      if (userAnswers.includes(null)) {
        alert('请完成所有题目后再提交！');
        return;
      }
      
      submitted = true;
      
      // 计算得分
      let correctCount = 0;
      quizData.forEach((q, idx) => {
        const isCorrect = userAnswers[idx] === q.correct;
        if (isCorrect) correctCount++;
        
        // 标记正确/错误答案
        const questionEl = wrap.querySelector(`[data-question="${idx}"].quiz-question`);
        const options = questionEl.querySelectorAll('.quiz-option');
        options.forEach((opt, optIdx) => {
          if (optIdx === q.correct) {
            opt.classList.add('correct');
          } else if (optIdx === userAnswers[idx] && !isCorrect) {
            opt.classList.add('incorrect');
          }
          opt.style.pointerEvents = 'none';
        });
      });
      
      // 显示结果
      const score = Math.round((correctCount / quizData.length) * 100);
      const resultEl = wrap.querySelector('#quizResult');
      resultEl.style.display = 'block';
      resultEl.innerHTML = `
        <div class="quiz-result">
          <div class="quiz-score">${score}分</div>
          <div class="quiz-message">
            你答对了 ${correctCount} / ${quizData.length} 题
            ${score >= 80 ? '🎉 太棒了！' : score >= 60 ? '👍 不错！继续加油！' : '💪 继续学习，你会更好！'}
          </div>
        </div>
      `;
      
      // 滚动到结果
      resultEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });

    // 重新开始
    const resetBtn = wrap.querySelector('#resetQuiz');
    resetBtn.addEventListener('click', () => {
      submitted = false;
      userAnswers = new Array(quizData.length).fill(null);
      renderPersonalizeSection(wrap);
    });
  }

  function renderCommentsSection(wrap) {
    // 留言区 - 类似微信公众号评论区
    // 使用全局变量存储留言数据，保持状态
    if (!window.commentsData) {
      window.commentsData = [
        {
          id: 1,
          author: "张三",
          avatar: "👨",
          content: "这个项目的去噪效果非常好！在低光照场景下表现尤其出色。",
          time: "2小时前",
          likes: 23,
          liked: false,
          expanded: false,
          replies: [
            {
              id: 11,
              author: "作者",
              avatar: "AI",
              content: "感谢支持！我们针对低光照场景做了专门的优化。",
              time: "1小时前",
              isAuthor: true
            }
          ]
        },
        {
          id: 2,
          author: "李四",
          avatar: "👩",
          content: "能否分享一下训练数据集的构建方法？我在复现过程中遇到了一些问题。",
          time: "5小时前",
          likes: 15,
          liked: false,
          expanded: false,
          replies: []
        },
        {
          id: 3,
          author: "王五",
          avatar: "🧑",
          content: "PSNR提升了2dB，这个结果很不错！期待后续更多的实验结果。",
          time: "1天前",
          likes: 8,
          liked: false,
          expanded: false,
          replies: [
            {
              id: 31,
              author: "作者",
              avatar: "AI",
              content: "谢谢！我们会继续优化模型，欢迎交流讨论。",
              time: "20小时前",
              isAuthor: true
            },
            {
              id: 32,
              author: "赵六",
              avatar: "👨",
              content: "请问在SIDD数据集上的表现如何？",
              time: "18小时前",
              isAuthor: false
            }
          ]
        }
      ];
    }
    const commentsData = window.commentsData;

    const commentsHTML = `
      <div class="comments-container">
        <div class="comments-header">
          <h2 class="comments-title">留言区</h2>
          <div class="comments-count">${commentsData.length} 条留言</div>
        </div>
        
        <div class="comment-input-area">
          <div class="comment-input-wrapper">
            <textarea class="comment-input" id="newCommentInput" placeholder="写下你的想法..."></textarea>
            <button class="btn btn--primary" id="submitComment">发表留言</button>
          </div>
        </div>

        <div class="comments-list" id="commentsList">
          ${commentsData.map(comment => `
            <div class="comment-item ${comment.expanded ? 'expanded' : ''}" data-id="${comment.id}">
              <div class="comment-avatar">${comment.avatar}</div>
              <div class="comment-body">
                <div class="comment-header">
                  <span class="comment-author">${comment.author}</span>
                  <span class="comment-time">${comment.time}</span>
                </div>
                <div class="comment-content">${comment.content}</div>
                <div class="comment-actions">
                  <button class="comment-action like-btn ${comment.liked ? 'liked' : ''}" data-id="${comment.id}">
                    <span class="action-icon">${comment.liked ? '❤️' : '🤍'}</span>
                    <span class="action-text">${comment.likes}</span>
                  </button>
                  <button class="comment-action expand-btn" data-id="${comment.id}">
                    <span class="action-icon">💬</span>
                    <span class="action-text">${comment.replies.length > 0 ? `${comment.replies.length} 条回复` : '回复'}</span>
                  </button>
                </div>
                
                <div class="comment-details" style="display: ${comment.expanded ? 'block' : 'none'};">
                  ${comment.replies.length > 0 ? `
                    <div class="comment-replies">
                      ${comment.replies.map(reply => `
                        <div class="reply-item ${reply.isAuthor ? 'author-reply' : ''}">
                          <div class="reply-avatar">${reply.avatar}</div>
                          <div class="reply-body">
                            <div class="reply-header">
                              <span class="reply-author">${reply.author}${reply.isAuthor ? ' <span class="author-badge">作者</span>' : ''}</span>
                              <span class="reply-time">${reply.time}</span>
                            </div>
                            <div class="reply-content">${reply.content}</div>
                          </div>
                        </div>
                      `).join('')}
                    </div>
                  ` : ''}
                  
                  <div class="reply-input-area" data-id="${comment.id}">
                    <div class="reply-input-wrapper">
                      <input type="text" class="reply-input" placeholder="写下你的回复..." />
                      <button class="btn btn--primary btn--small send-reply-btn">发送</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    wrap.innerHTML = commentsHTML;

    // 发表新留言
    const submitCommentBtn = wrap.querySelector('#submitComment');
    const newCommentInput = wrap.querySelector('#newCommentInput');
    submitCommentBtn.addEventListener('click', () => {
      const content = newCommentInput.value.trim();
      if (!content) {
        alert('请输入留言内容');
        return;
      }
      
      const newComment = {
        id: Date.now(),
        author: "你",
        avatar: "👤",
        content: content,
        time: "刚刚",
        likes: 0,
        liked: false,
        replies: []
      };
      
      commentsData.unshift(newComment);
      newCommentInput.value = '';
      renderCommentsSection(wrap);
    });

    // 点赞功能
    const likeBtns = wrap.querySelectorAll('.like-btn');
    likeBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const commentId = parseInt(btn.dataset.id);
        const comment = commentsData.find(c => c.id === commentId);
        if (comment) {
          comment.liked = !comment.liked;
          comment.likes += comment.liked ? 1 : -1;
          btn.classList.toggle('liked');
          btn.querySelector('.action-icon').textContent = comment.liked ? '❤️' : '🤍';
          btn.querySelector('.action-text').textContent = comment.likes;
        }
      });
    });

    // 展开/收起回复
    const expandBtns = wrap.querySelectorAll('.expand-btn');
    expandBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const commentId = parseInt(btn.dataset.id);
        const comment = commentsData.find(c => c.id === commentId);
        const commentItem = wrap.querySelector(`.comment-item[data-id="${commentId}"]`);
        const detailsArea = commentItem.querySelector('.comment-details');
        
        if (comment) {
          comment.expanded = !comment.expanded;
          commentItem.classList.toggle('expanded');
          detailsArea.style.display = comment.expanded ? 'block' : 'none';
          
          if (comment.expanded) {
            const replyInput = detailsArea.querySelector('.reply-input');
            setTimeout(() => replyInput?.focus(), 100);
          }
        }
      });
    });

    // 发送回复
    const sendReplyBtns = wrap.querySelectorAll('.send-reply-btn');
    sendReplyBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const replyArea = btn.closest('.reply-input-area');
        const commentId = parseInt(replyArea.dataset.id);
        const replyInput = replyArea.querySelector('.reply-input');
        const content = replyInput.value.trim();
        
        if (!content) {
          alert('请输入回复内容');
          return;
        }
        
        const comment = commentsData.find(c => c.id === commentId);
        if (comment) {
          comment.replies.push({
            id: Date.now(),
            author: "你",
            avatar: "👤",
            content: content,
            time: "刚刚",
            isAuthor: false
          });
          
          replyInput.value = '';
          replyArea.style.display = 'none';
          renderCommentsSection(wrap);
        }
      });
    });
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

  if (searchInput) {
  searchInput.addEventListener('input', performSearch);
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      performSearch();
    }
  });
  }
  if (searchBtn) {
    searchBtn.addEventListener('click', performSearch);
  }

  // 登录和注册功能
  const loginBtns = qsa('.login-btn');
  const roleCards = qsa('.role__card');

  // 首页登录按钮 - 直接显示登录表单
  if (loginBtn) {
    loginBtn.addEventListener('click', () => {
      showLoginForm();
      if (loginModal) loginModal.classList.add('active');
    });
  }

  // 首页注册按钮
  if (registerBtn) {
    registerBtn.addEventListener('click', () => {
      if (registerModal) registerModal.classList.add('active');
    });
  }

  // 侧边栏登录按钮（如果有）
  loginBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      if (loginModal) loginModal.classList.add('active');
    });
  });

  // 关闭登录模态框
  if (closeLoginModal) {
    closeLoginModal.addEventListener('click', () => {
      if (loginModal) loginModal.classList.remove('active');
    });
  }

  // 关闭注册模态框
  if (closeRegisterModal) {
    closeRegisterModal.addEventListener('click', () => {
      if (registerModal) registerModal.classList.remove('active');
    });
  }

  // 点击背景关闭模态框
  if (loginModal) {
    loginModal.addEventListener('click', (e) => {
      if (e.target === loginModal || e.target.classList.contains('modal__overlay')) {
        loginModal.classList.remove('active');
      }
    });
  }

  if (registerModal) {
    registerModal.addEventListener('click', (e) => {
      if (e.target === registerModal || e.target.classList.contains('modal__overlay')) {
        registerModal.classList.remove('active');
      }
    });
  }

  // 切换到登录
  if (switchToLogin) {
    switchToLogin.addEventListener('click', (e) => {
      e.preventDefault();
      if (registerModal) registerModal.classList.remove('active');
      if (loginModal) loginModal.classList.add('active');
    });
  }

  // 注册表单提交
  if (registerForm) {
    registerForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      const username = formData.get('username') || e.target.querySelector('input[type="text"]').value;
      const email = formData.get('email') || e.target.querySelector('input[type="email"]').value;
      const passwords = e.target.querySelectorAll('input[type="password"]');
      const password = passwords[0].value;
      const confirmPassword = passwords[1].value;
      const role = formData.get('role') || e.target.querySelector('select').value;
      
      // 验证
      if (!username || !email || !password || !role) {
        alert('请填写完整信息！');
        return;
      }
      
      if (password !== confirmPassword) {
        alert('两次输入的密码不一致！');
        return;
      }
      
      if (password.length < 6) {
        alert('密码长度至少6位！');
        return;
      }
      
      // 注册
      const result = registerUser(username, email, password, role);
      if (result.success) {
      alert('注册成功！请登录');
      if (registerModal) registerModal.classList.remove('active');
        showLoginForm();
      if (loginModal) loginModal.classList.add('active');
      } else {
        alert(result.message);
      }
    });
  }

  // 注册功能 - 使用localStorage存储账号信息
  function registerUser(username, email, password, role) {
    // 获取现有用户
    const users = JSON.parse(localStorage.getItem('platform_users') || '[]');
    
    // 检查用户名是否已存在
    if (users.find(u => u.username === username)) {
      return { success: false, message: '用户名已存在！' };
    }
    
    // 检查邮箱是否已存在
    if (users.find(u => u.email === email)) {
      return { success: false, message: '邮箱已被注册！' };
    }
    
    // 添加新用户
    users.push({
      username: username,
      email: email,
      password: password, // 实际项目中应该加密
      role: role,
      createdAt: new Date().toISOString()
    });
    
    localStorage.setItem('platform_users', JSON.stringify(users));
    return { success: true, message: '注册成功！' };
  }

  // 登录验证
  function loginUser(username, password) {
    const users = JSON.parse(localStorage.getItem('platform_users') || '[]');
    const user = users.find(u => u.username === username && u.password === password);
    
    if (user) {
      return { success: true, user: user };
    } else {
      return { success: false, message: '用户名或密码错误！' };
    }
  }

  // 显示登录表单
  function showLoginForm() {
    if (!loginModal) return;
    
    const modalContent = loginModal.querySelector('.modal__content');
    modalContent.innerHTML = `
      <button class="modal__close" id="closeLoginModal2">×</button>
      <h2 class="modal__title">登录账号</h2>
      <form class="register__form" id="loginForm">
        <div class="form__group">
          <label class="form__label">用户名</label>
          <input type="text" name="username" class="input input--full" placeholder="请输入用户名" required />
        </div>
        <div class="form__group">
          <label class="form__label">密码</label>
          <input type="password" name="password" class="input input--full" placeholder="请输入密码" required />
        </div>
        <button type="submit" class="btn btn--primary btn--large" style="width: 100%; margin-top: 12px;">登录</button>
        <div class="form__footer">
          还没有账号？<a href="#" id="switchToRegister">立即注册</a>
        </div>
      </form>
    `;
    
    // 重新绑定关闭按钮
    const closeBtn = modalContent.querySelector('#closeLoginModal2');
    closeBtn.addEventListener('click', () => {
      loginModal.classList.remove('active');
    });
    
    // 绑定登录表单
    const loginForm = modalContent.querySelector('#loginForm');
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      const username = formData.get('username');
      const password = formData.get('password');
      
      const result = loginUser(username, password);
      if (result.success) {
        handleLogin(result.user.role, result.user.username);
        loginModal.classList.remove('active');
        alert('登录成功！');
      } else {
        alert(result.message);
      }
    });
    
    // 切换到注册
    const switchToReg = modalContent.querySelector('#switchToRegister');
    switchToReg.addEventListener('click', (e) => {
      e.preventDefault();
      loginModal.classList.remove('active');
      if (registerModal) registerModal.classList.add('active');
    });
  }

  // 角色选择登录（改为显示登录表单）
  roleCards.forEach(card => {
    card.addEventListener('click', () => {
      if (loginModal) loginModal.classList.remove('active');
      // 直接显示登录表单
      setTimeout(() => {
        showLoginForm();
        loginModal.classList.add('active');
      }, 100);
    });
  });

  function handleLogin(role, username) {
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
      el.textContent = `已登录 · ${roleNames[role]} · ${username}`;
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
  const qaFilesBtn = document.getElementById('qaFilesBtn');
  let hasGeneratedFiles = false;

  // 模拟生成的文件数据
  const generatedFiles = [
    {
      id: 1,
      name: 'model_architecture.py',
      type: 'Python',
      size: '3.2 KB',
      time: '刚刚',
      content: `# 模型架构定义
import torch
import torch.nn as nn

class DenoiseModel(nn.Module):
    def __init__(self, in_channels=3, out_channels=3):
        super(DenoiseModel, self).__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(in_channels, 64, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, 3, padding=1),
            nn.ReLU(inplace=True)
        )
        self.decoder = nn.Sequential(
            nn.Conv2d(64, 64, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, out_channels, 3, padding=1)
        )
    
    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x`
    },
    {
      id: 2,
      name: 'train.py',
      type: 'Python',
      size: '5.8 KB',
      time: '刚刚',
      content: `# 训练脚本
import torch
from torch.utils.data import DataLoader
from model_architecture import DenoiseModel

def train_model(model, dataloader, epochs=100):
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    criterion = torch.nn.MSELoss()
    
    for epoch in range(epochs):
        for batch in dataloader:
            noisy, clean = batch
            output = model(noisy)
            loss = criterion(output, clean)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        
        print(f'Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}')

if __name__ == '__main__':
    model = DenoiseModel()
    # 初始化数据加载器
    train_model(model, dataloader)`
    },
    {
      id: 3,
      name: 'requirements.txt',
      type: 'Text',
      size: '0.5 KB',
      time: '刚刚',
      content: `torch>=2.0.0
torchvision>=0.15.0
numpy>=1.24.0
opencv-python>=4.8.0
pillow>=10.0.0
tqdm>=4.65.0
tensorboard>=2.13.0`
    }
  ];

  // 切换到聊天界面
  function switchToChat(initialQuery = null) {
    const qaWelcome = document.getElementById('qaWelcome');
    const qaChat = document.getElementById('qaChat');
    
    if (qaWelcome) qaWelcome.style.display = 'none';
    if (qaChat) qaChat.style.display = 'grid';
    
    // 如果有初始查询，发送它
    if (initialQuery) {
      qaInput.value = initialQuery;
      sendQaMessage();
    }
  }

  // 绑定欢迎页面的输入框和发送按钮
  const qaWelcomeInput = document.getElementById('qaWelcomeInput');
  const qaWelcomeSendBtn = document.getElementById('qaWelcomeSendBtn');
  
  if (qaWelcomeSendBtn) {
    qaWelcomeSendBtn.addEventListener('click', () => {
      const query = qaWelcomeInput?.value?.trim();
      if (query) {
        switchToChat(query);
      }
    });
  }
  
  if (qaWelcomeInput) {
    qaWelcomeInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const query = qaWelcomeInput.value.trim();
        if (query) {
          switchToChat(query);
        }
      }
    });
  }

  function sendQaMessage() {
    const text = (qaInput?.value || '').trim();
    if (!text) return;
    
    // 确保已切换到聊天界面
    const qaWelcome = document.getElementById('qaWelcome');
    const qaChat = document.getElementById('qaChat');
    if (qaWelcome && qaWelcome.style.display !== 'none') {
      switchToChat();
    }
    
    qaMessages.insertAdjacentHTML('beforeend', `<div class="msg msg--user">
      <div class="msg__avatar">你</div>
      <div class="msg__bubble">
        <div class="msg__content">${text}</div>
      </div>
    </div>`);
    
    // 模拟AI回复
    setTimeout(() => {
    qaMessages.insertAdjacentHTML('beforeend', `<div class="msg msg--ai">
      <div class="msg__avatar">AI</div>
      <div class="msg__bubble">
          <div class="msg__content">我已经为你生成了完整的代码框架，包括模型架构定义、训练脚本和依赖配置文件。你可以点击右上角的"文件"按钮查看和下载这些文件。</div>
      </div>
    </div>`);
      qaMessages.scrollTop = qaMessages.scrollHeight;
      
      // 显示文件按钮
      if (qaFilesBtn && !hasGeneratedFiles) {
        qaFilesBtn.style.display = 'flex';
        hasGeneratedFiles = true;
      }
    }, 1000);
    
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

  // 文件查看功能
  const filesModal = document.getElementById('filesModal');
  const closeFilesModal = document.getElementById('closeFilesModal');
  const filesList = document.getElementById('filesList');

  if (qaFilesBtn) {
    qaFilesBtn.addEventListener('click', () => {
      if (filesModal) {
        renderFilesList();
        filesModal.classList.add('active');
      }
    });
  }

  if (closeFilesModal) {
    closeFilesModal.addEventListener('click', () => {
      if (filesModal) filesModal.classList.remove('active');
    });
  }

  if (filesModal) {
    filesModal.addEventListener('click', (e) => {
      if (e.target === filesModal || e.target.classList.contains('modal__overlay')) {
        filesModal.classList.remove('active');
      }
    });
  }

  function renderFilesList() {
    if (!filesList) return;
    
    filesList.innerHTML = generatedFiles.map(file => `
      <div class="file-item">
        <div class="file-info">
          <div class="file-name">${file.name}</div>
          <div class="file-meta">${file.type} · ${file.size} · ${file.time}</div>
          <div class="file-preview" style="display: none;" data-id="${file.id}">
            <pre style="margin: 0; white-space: pre-wrap;">${file.content}</pre>
          </div>
        </div>
        <div class="file-actions">
          <button class="btn btn--ghost btn--small preview-file-btn" data-id="${file.id}">预览</button>
          <button class="btn btn--primary btn--small download-file-btn" data-id="${file.id}">下载</button>
        </div>
      </div>
    `).join('');

    // 绑定预览按钮
    const previewBtns = filesList.querySelectorAll('.preview-file-btn');
    previewBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const fileId = parseInt(btn.dataset.id);
        const preview = filesList.querySelector(`.file-preview[data-id="${fileId}"]`);
        if (preview) {
          const isVisible = preview.style.display !== 'none';
          preview.style.display = isVisible ? 'none' : 'block';
          btn.textContent = isVisible ? '预览' : '收起';
        }
      });
    });

    // 绑定下载按钮
    const downloadBtns = filesList.querySelectorAll('.download-file-btn');
    downloadBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const fileId = parseInt(btn.dataset.id);
        const file = generatedFiles.find(f => f.id === fileId);
        if (file) {
          const blob = new Blob([file.content], { type: 'text/plain' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = file.name;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }
      });
    });
  }

  // 划词工具栏功能
  const textToolbar = document.getElementById('textToolbar');
  const askAIBtn = document.getElementById('askAI');
  const highlightTextBtn = document.getElementById('highlightText');
  const highlightColors = document.getElementById('highlightColors');
  const underlineTextBtn = document.getElementById('underlineText');
  const strikeTextBtn = document.getElementById('strikeText');
  
  let selectedText = '';
  let selectedRange = null;

  // 监听文本选择
  document.addEventListener('mouseup', (e) => {
    const selection = window.getSelection();
    const text = selection.toString().trim();
    
    if (text && text.length > 0) {
      selectedText = text;
      selectedRange = selection.getRangeAt(0);
      
      // 显示工具栏
      const rect = selectedRange.getBoundingClientRect();
      textToolbar.style.display = 'flex';
      textToolbar.style.left = `${rect.left + window.scrollX + (rect.width / 2) - 100}px`;
      textToolbar.style.top = `${rect.top + window.scrollY - 45}px`;
    } else {
      textToolbar.style.display = 'none';
      highlightColors.style.display = 'none';
    }
  });

  // 点击其他地方关闭工具栏
  document.addEventListener('mousedown', (e) => {
    if (!textToolbar.contains(e.target) && !e.target.closest('.markdown-rendered')) {
      textToolbar.style.display = 'none';
      highlightColors.style.display = 'none';
    }
  });

  // 询问AI
  if (askAIBtn) {
    askAIBtn.addEventListener('click', () => {
      if (selectedText) {
        // 切换到AI聊天界面
        switchToChat(selectedText);
        textToolbar.style.display = 'none';
        window.getSelection().removeAllRanges();
      }
    });
  }

  // 高亮按钮
  if (highlightTextBtn) {
    highlightTextBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      highlightColors.style.display = highlightColors.style.display === 'none' ? 'flex' : 'none';
    });
  }

  // 颜色选择
  if (highlightColors) {
    const colorOptions = highlightColors.querySelectorAll('.color-option');
    colorOptions.forEach(option => {
      option.addEventListener('click', (e) => {
        e.stopPropagation();
        const color = option.dataset.color;
        applyHighlight(color);
        highlightColors.style.display = 'none';
        textToolbar.style.display = 'none';
      });
    });
  }

  // 下划线
  if (underlineTextBtn) {
    underlineTextBtn.addEventListener('click', () => {
      applyUnderline();
      textToolbar.style.display = 'none';
    });
  }

  // 删除线
  if (strikeTextBtn) {
    strikeTextBtn.addEventListener('click', () => {
      applyStrikethrough();
      textToolbar.style.display = 'none';
    });
  }

  function applyHighlight(color) {
    if (!selectedRange) return;
    
    try {
      const span = document.createElement('span');
      span.className = 'text-highlight';
      span.style.backgroundColor = color;
      
      // 更安全的包裹方法
      const contents = selectedRange.extractContents();
      span.appendChild(contents);
      selectedRange.insertNode(span);
      
      saveAnnotations();
      window.getSelection().removeAllRanges();
    } catch (e) {
      console.error('应用高亮失败:', e);
      // 备用方法：使用document.execCommand
      try {
        document.execCommand('backColor', false, color);
        saveAnnotations();
      } catch (e2) {
        console.error('备用方法也失败:', e2);
      }
    }
  }

  function applyUnderline() {
    if (!selectedRange) return;
    
    try {
      const span = document.createElement('span');
      span.className = 'text-underline';
      
      const contents = selectedRange.extractContents();
      span.appendChild(contents);
      selectedRange.insertNode(span);
      
      saveAnnotations();
      window.getSelection().removeAllRanges();
    } catch (e) {
      console.error('应用下划线失败:', e);
      try {
        document.execCommand('underline', false, null);
        saveAnnotations();
      } catch (e2) {
        console.error('备用方法也失败:', e2);
      }
    }
  }

  function applyStrikethrough() {
    if (!selectedRange) return;
    
    try {
      const span = document.createElement('span');
      span.className = 'text-strike';
      
      const contents = selectedRange.extractContents();
      span.appendChild(contents);
      selectedRange.insertNode(span);
      
      saveAnnotations();
      window.getSelection().removeAllRanges();
    } catch (e) {
      console.error('应用删除线失败:', e);
      try {
        document.execCommand('strikeThrough', false, null);
        saveAnnotations();
      } catch (e2) {
        console.error('备用方法也失败:', e2);
      }
    }
  }

  function saveAnnotations() {
    // 保存标注到localStorage
    const content = document.getElementById('detailContent');
    if (content) {
      const html = content.innerHTML;
      localStorage.setItem('notebook_annotations', html);
    }
  }

  function loadAnnotations() {
    // 加载保存的标注
    const saved = localStorage.getItem('notebook_annotations');
    const content = document.getElementById('detailContent');
    if (saved && content) {
      content.innerHTML = saved;
    }
  }

  // 初始化
  showHomeView();
  // 恢复主题
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.body.classList.remove('theme-light');
    document.body.classList.add('theme-dark');
  }
})();


