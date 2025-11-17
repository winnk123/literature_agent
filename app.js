(function () {
  const qs = (s, r = document) => r.querySelector(s);
  const qsa = (s, r = document) => Array.from(r.querySelectorAll(s));

  const homeView = qs('#home-view');
  const detailView = qs('#detail-view');
  const createViewGlobal = qs('#create-view');  // 用于视图切换
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
  // 暴露到全局（供模块使用）
  window.currentUserRole = currentUserRole;

  const notebookSessionId = (() => {
    try {
      const stored = localStorage.getItem('notebookSessionId');
      if (stored) return stored;
      const newId = `nb-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
      localStorage.setItem('notebookSessionId', newId);
      return newId;
    } catch (e) {
      console.warn('Notebook Session 初始化失败，使用临时ID');
      return `nb-${Date.now()}`;
    }
  })();

  // 统一获取后端 API 基地址：
  // 优先级：localStorage('apiBaseUrl') > window.API_BASE_URL > 同源 > 'http://localhost:5000'
  function getApiBaseUrl() {
    try {
      const fromStorage = (typeof localStorage !== 'undefined') ? localStorage.getItem('apiBaseUrl') : null;
      if (fromStorage && typeof fromStorage === 'string') {
        return fromStorage.replace(/\/+$/, '');
      }
      const fromWindow = (typeof window !== 'undefined') ? window.API_BASE_URL : null;
      if (fromWindow && typeof fromWindow === 'string') {
        return fromWindow.replace(/\/+$/, '');
      }
      if (typeof window !== 'undefined' && window.location && window.location.protocol !== 'file:') {
        return `${window.location.protocol}//${window.location.host}`.replace(/\/+$/, '');
      }
    } catch (e) {
      // ignore and fallback below
    }
    return 'http://localhost:5000';
  }

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
    // 检查权限
    if (currentUserRole === 'enterprise' || currentUserRole === 'teacher') {
      // 跳转到出题页面
      history.pushState({ view: 'create' }, '', '#create');
      switchView('create');
      // 重置表单
      const form = qs('#createProblemForm');
      if (form) form.reset();
    } else if (currentUserRole) {
      alert('您没有出题权限，只有企业或高校教师可以出题。');
    } else {
      // 未登录，显示登录模态框
      if (loginModal) loginModal.classList.add('active');
    }
  });

  // ============================================
  // 渲染器注册表 - Renderer Registry
  // ============================================
  // 说明: 将章节类型映射到对应的渲染函数，支持动态注册
  
  window.RendererRegistry = {
    // Notebook渲染器
    notebook: function(sectionKey, content, project) {
      const sectionConfig = window.ProjectStructureConfig?.getSection(sectionKey);
      const cells = content || sectionConfig?.notebookConfig?.defaultCells || [];
      renderNotebook('detailContent', cells);
    },
    
    // 个性化检验渲染器
    quiz: function(sectionKey, content, project) {
      const sectionConfig = window.ProjectStructureConfig?.getSection(sectionKey);
      const quizData = content || sectionConfig?.quizConfig?.defaultQuizData || [];
      const wrap = document.getElementById('detailContent');
      if (wrap) {
        renderPersonalizeSection(wrap, quizData);
      }
    },
    
    // 留言区渲染器
    comments: function(sectionKey, content, project) {
      const sectionConfig = window.ProjectStructureConfig?.getSection(sectionKey);
      const initialComments = content || sectionConfig?.commentsConfig?.defaultInitialComments || [];
      const wrap = document.getElementById('detailContent');
      if (wrap) {
        renderCommentsSection(wrap, initialComments);
      }
    },
    
    // 自定义渲染器（通过函数名调用）
    custom: function(sectionKey, content, project) {
      const sectionConfig = window.ProjectStructureConfig?.getSection(sectionKey);
      const rendererName = sectionConfig?.customRenderer;
      
      if (!rendererName) {
        console.warn(`[RendererRegistry] 章节 "${sectionKey}" 未指定自定义渲染器`);
        return;
      }
      
      const wrap = document.getElementById('detailContent');
      if (!wrap) {
        console.error(`[RendererRegistry] detailContent 元素未找到`);
        return;
      }
      
      // 尝试从全局作用域获取渲染器函数
      const renderer = window[rendererName];
      
      if (typeof renderer === 'function') {
        try {
          // 小频道等自定义渲染器只需要wrap参数
          renderer(wrap);
        } catch (e) {
          console.error(`[RendererRegistry] 自定义渲染器 "${rendererName}" 调用失败:`, e);
          wrap.innerHTML = `<p>渲染出错: ${e.message}</p>`;
        }
      } else {
        console.error(`[RendererRegistry] 自定义渲染器 "${rendererName}" 未找到或不是函数`);
        wrap.innerHTML = `<p>渲染器 "${rendererName}" 未找到</p>`;
      }
    },
    
    // 注册新的渲染器
    register: function(type, renderer) {
      if (typeof renderer !== 'function') {
        console.error(`[RendererRegistry] 渲染器必须是函数`);
        return;
      }
      this[type] = renderer;
      console.log(`[RendererRegistry] 已注册渲染器: ${type}`);
    }
  };

  // ============================================
  // 数据管理模块 - Data Management Module
  // ============================================
  // 说明: 管理项目和分类数据，支持 localStorage 持久化
  
  const STORAGE_KEY_PROJECTS = 'ai_platform_projects';
  
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

  // 默认项目数据（作为初始数据）
  const defaultProjects = [
    { id: 'p1', category: 'image', subKey: 'cam-denoise', title: '相机的图像去噪 · 实验版', desc: '复杂背景下的高保真去噪。', likes: 128, status: 'approved' },
    { id: 'p6', category: 'image', subKey: 'photo-restore', title: '照片的图像修复 · 划痕', desc: '老照片划痕修复与细节重建。', likes: 64, status: 'approved' },
    { id: 'p2', category: 'audio', subKey: 'speech-enhance', title: '语音增强 · 远场', desc: '远场语音的清晰化处理。', likes: 76, status: 'approved' },
    { id: 'p7', category: 'audio', subKey: 'speech-separate', title: '语音分离 · 鸣噪', desc: '音乐与语音的自适应分离。', likes: 58, status: 'approved' },
    { id: 'p3', category: 'llm', subKey: 'knowledge-retrieval', title: 'LLM · 知识检索', desc: '检索增强生成。', likes: 203, status: 'approved' },
    { id: 'p8', category: 'llm', subKey: 'code-assistant', title: 'LLM · 代码助手', desc: '上下文感知的编程辅助。', likes: 312, status: 'approved' },
    { id: 'p4', category: 'mllm', subKey: 'vision-language', title: 'MLLM · 图文理解', desc: '多模态语义对齐与问答。', likes: 97, status: 'approved' },
    { id: 'p5', category: 'agent', subKey: 'research-agent', title: 'Agent · 科研助手', desc: '工作流编排与自动化研究。', likes: 141, status: 'approved' }
  ];
  
  /**
   * 初始化项目数据
   * 从 localStorage 加载，如果没有则使用默认数据
   */
  function initProjectsData() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY_PROJECTS);
      
      if (stored) {
        // 使用存储的数据
        const storedProjects = JSON.parse(stored);
        console.log('[DataManagement] 从 localStorage 加载项目，数量:', storedProjects.length);
        return storedProjects;
      } else {
        // 使用默认数据并保存
        console.log('[DataManagement] 使用默认项目数据并保存到 localStorage');
        localStorage.setItem(STORAGE_KEY_PROJECTS, JSON.stringify(defaultProjects));
        return defaultProjects;
      }
    } catch (e) {
      console.error('[DataManagement] 初始化项目数据失败:', e);
      return defaultProjects;
    }
  }
  
  // 初始化项目列表（从 localStorage 或默认数据）
  const projects = initProjectsData();
  
  // 暴露到全局（供其他模块使用）
  window.projects = projects;
  
  /**
   * 监听项目更新事件
   * 当新项目被审核通过后，自动更新项目列表
   */
  window.addEventListener('projectsUpdated', (e) => {
    const { projects: newProjects } = e.detail;
    console.log('[DataManagement] 接收到项目更新事件，新项目数量:', newProjects.length);
    
    // 更新 localStorage
    try {
      localStorage.setItem(STORAGE_KEY_PROJECTS, JSON.stringify(newProjects));
    } catch (err) {
      console.error('[DataManagement] 保存项目到 localStorage 失败:', err);
    }
    
    // 更新全局 projects 数组
    window.projects.length = 0;
    window.projects.push(...newProjects);
    
    // 如果当前在项目视图，重新渲染
    if (projectsView && projectsView.classList.contains('is-active')) {
      renderCards(window.projects);
    }
    
    // 更新左侧导航列表
    if (typeof renderProjectsList === 'function') {
      renderProjectsList();
    }
    
    console.log('[DataManagement] 项目列表已更新 ✓');
  });

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
  
  // 暴露到全局（供模块使用）
  window.showHomeView = showHomeView;

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

    // 设置当前项目ID到全局变量
    window.currentProjectId = project.id;

    renderDetailSection('background', project);
    switchView('detail');
    history.pushState({ view: 'detail', id: project.id, section: 'background' }, '', `#project/${project.id}/background`);
    
    // 加载该项目的历史会话和文件
    loadConversationHistory(project.id);
    loadFilesFromStorage();
    
    // 如果有历史会话，显示对话界面；否则显示欢迎页面
    const qaWelcome = document.getElementById('qaWelcome');
    const qaChat = document.getElementById('qaChat');
    const hasHistory = checkHasConversationHistory(project.id);
    
    if (hasHistory) {
      if (qaWelcome) qaWelcome.style.display = 'none';
      if (qaChat) qaChat.style.display = 'grid';
    } else {
    if (qaWelcome) qaWelcome.style.display = 'flex';
    if (qaChat) qaChat.style.display = 'none';
    }
  }

  function buildDetailMenu(project) {
    const menu = document.getElementById('detailMenu');
    menu.innerHTML = '';
    
    // 从配置获取章节结构
    if (!window.ProjectStructureConfig) {
      console.warn('[buildDetailMenu] ProjectStructureConfig 未加载，使用默认结构');
      // 回退到默认结构
      const groups = [
        { key: 'background', name: '背景' },
        { key: 'model', name: '模型', children: [
          { key: 'model-intro', name: '模型介绍' },
          { key: 'baseline', name: 'baseline 介绍' }
        ]},
        { key: 'idea', name: 'IDEA 引导' },
        { key: 'personalize', name: '个性化检验' },
        { key: 'comments', name: '留言区' },
        { key: 'channels', name: '小频道' }
      ];
      buildMenuFromGroups(menu, groups, project);
      return;
    }
    
    const rootSections = window.ProjectStructureConfig.getRootSections();
    const groups = rootSections.map(section => {
      const childSections = window.ProjectStructureConfig.getChildSections(section.key);
      return {
        key: section.key,
        name: section.name,
        children: childSections.length > 0 ? childSections.map(c => ({ key: c.key, name: c.name })) : undefined
      };
    });
    
    buildMenuFromGroups(menu, groups, project);
  }
  
  // 辅助函数：从groups数组构建菜单
  function buildMenuFromGroups(menu, groups, project) {

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
              renderDetailSection(c.key, project);
              history.pushState({ view: 'detail', id: project.id, section: c.key }, '', `#project/${project.id}/${c.key}`);
            });
            sub.appendChild(sli);
          });
          li.appendChild(sub);
        });
      } else {
        btn.addEventListener('click', () => {
          renderDetailSection(g.key, project);
          history.pushState({ view: 'detail', id: project.id, section: g.key }, '', `#project/${project.id}/${g.key}`);
        });
      }
      ul.appendChild(li);
    });
    menu.appendChild(ul);
  }
  
  // 获取当前项目
  function getCurrentProject() {
    const projectId = window.currentProjectId;
    if (!projectId) return null;
    
    const projects = window.projects || [];
    return projects.find(p => p.id === projectId) || null;
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
      language: type === 'code' ? language : null,
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
          <label for="cell-input-${cell.id}" class="sr-only">代码输入</label>
          <textarea id="cell-input-${cell.id}" name="cellCode" class="cell-input" placeholder="在此输入代码..." autocomplete="off">${cell.content}</textarea>
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
          <label for="cell-input-md-${cell.id}" class="sr-only">Markdown输入</label>
          <textarea id="cell-input-md-${cell.id}" name="cellMarkdown" class="cell-input" style="display: none;" autocomplete="off">${cell.content}</textarea>
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
      // 支持 Tab 键缩进
      textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
          e.preventDefault();
          const start = textarea.selectionStart;
          const end = textarea.selectionEnd;
          const value = textarea.value;
          textarea.value = value.substring(0, start) + '    ' + value.substring(end);
          textarea.selectionStart = textarea.selectionEnd = start + 4;
          cell.content = textarea.value;
        }
      });
      
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
      runBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        runBtn.classList.add('is-running');
        try {
          await runCell(cell, cellDiv);
        } finally {
          runBtn.classList.remove('is-running');
        }
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

  function addCellAbove(cellId, type = 'code') {
    const idx = notebookCells.findIndex(c => c.id === cellId);
    const newCell = createNotebookCell(type, '', type === 'code' ? 'python' : null);
    notebookCells.splice(idx, 0, newCell);
    rerenderNotebook();
  }

  function addCellBelow(cellId, type = 'code') {
    const idx = notebookCells.findIndex(c => c.id === cellId);
    const newCell = createNotebookCell(type, '', type === 'code' ? 'python' : null);
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

  async function runNotebookCode(code, language = 'python') {
    const API_BASE_URL = getApiBaseUrl();
    const payload = {
      code,
      language,
      sessionId: notebookSessionId
    };
    const response = await fetch(`${API_BASE_URL}/api/notebook/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await response.json();
    return { status: response.status, result };
  }

  async function resetNotebookSession() {
    try {
      const API_BASE_URL = getApiBaseUrl();
      await fetch(`${API_BASE_URL}/api/notebook/session/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId: notebookSessionId })
      });
      pythonEnv.variables = {};
      pythonEnv.functions = {};
      alert('Notebook 会话已重置');
    } catch (error) {
      console.error('重置 Notebook 会话失败:', error);
      alert('Notebook 会话重置失败，请稍后再试');
    }
  }

  async function runCell(cell, cellDiv) {
    const code = cell.content.trim();
    if (!code) return;
    
    let output = '';
    let hasError = false;
    
    try {
      const { result } = await runNotebookCode(code, cell.language || 'python');
      if (result.success) {
        output = result.output && result.output.length ? result.output : '执行完成';
      } else {
        hasError = true;
        const pieces = [];
        if (result.output) pieces.push(result.output);
        if (result.message) pieces.push(result.message);
        if (result.traceback) pieces.push(result.traceback);
        output = pieces.filter(Boolean).join('\n').trim() || '执行失败';
      }
    } catch (error) {
      console.warn('Notebook 远程执行失败，使用本地模拟环境', error);
      output = executeCode(cell);
      hasError = output.startsWith('错误:');
    }

    cell.output = output;
    
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
        
        if (hasError) {
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
    const notebookShell = document.createElement('div');
    notebookShell.className = 'notebook-shell';

    const notebookToolbar = document.createElement('div');
    notebookToolbar.className = 'notebook-toolbar';
    notebookToolbar.innerHTML = `
      <div class="notebook-toolbar__info">
        <div class="notebook-toolbar__title">交互式 Notebook</div>
        <div class="notebook-toolbar__subtitle">Python · PyTorch (轻量代码)</div>
      </div>
      <div class="notebook-toolbar__actions">
        <button class="notebook-action" id="nbRunAll">运行全部</button>
        <button class="notebook-action" id="nbAddCode">+ 代码单元格</button>
        <button class="notebook-action" id="nbAddMarkdown">+ Markdown 文本</button>
        <div class="notebook-settings">
          <button class="notebook-action notebook-action--ghost" id="nbSettingsToggle">设置</button>
          <div class="notebook-settings__panel" id="nbSettingsPanel">
            <p>Notebook 设置</p>
            <button data-action="add-code">新增代码单元格</button>
            <button data-action="add-markdown">新增 Markdown 单元格</button>
            <button data-action="reset-session">重置 Python 会话</button>
          </div>
        </div>
      </div>
    `;

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
    notebookShell.appendChild(notebookToolbar);
    notebookShell.appendChild(notebookDiv);
    container.appendChild(notebookShell);

    const nbRunAllBtn = notebookToolbar.querySelector('#nbRunAll');
    const nbAddCodeBtn = notebookToolbar.querySelector('#nbAddCode');
    const nbAddMarkdownBtn = notebookToolbar.querySelector('#nbAddMarkdown');
    const nbSettingsToggle = notebookToolbar.querySelector('#nbSettingsToggle');
    const nbSettingsPanel = notebookToolbar.querySelector('#nbSettingsPanel');

    if (nbRunAllBtn) {
      nbRunAllBtn.addEventListener('click', async () => {
        nbRunAllBtn.disabled = true;
        nbRunAllBtn.textContent = '运行中...';
        try {
          await runAllCodeCells();
        } finally {
          nbRunAllBtn.disabled = false;
          nbRunAllBtn.textContent = '运行全部';
        }
      });
    }
    if (nbAddCodeBtn) {
      nbAddCodeBtn.addEventListener('click', () => {
        createNotebookCell('code', '', 'python');
        rerenderNotebook();
      });
    }
    if (nbAddMarkdownBtn) {
      nbAddMarkdownBtn.addEventListener('click', () => {
        createNotebookCell('markdown', '## Markdown 笔记\n在这里记录你的思考与观察。');
        rerenderNotebook();
      });
    }
    if (nbSettingsToggle && nbSettingsPanel) {
      nbSettingsToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        nbSettingsPanel.classList.toggle('is-visible');
        if (nbSettingsPanel.classList.contains('is-visible')) {
          setTimeout(() => {
            const closePanel = (evt) => {
              if (!nbSettingsPanel.contains(evt.target) && evt.target !== nbSettingsToggle) {
                nbSettingsPanel.classList.remove('is-visible');
              }
            };
            document.addEventListener('click', closePanel, { once: true });
          }, 0);
        }
      });
      const settingButtons = nbSettingsPanel.querySelectorAll('button[data-action]');
      settingButtons.forEach(btn => {
        btn.addEventListener('click', () => {
          const action = btn.dataset.action;
          if (action === 'add-code') {
            createNotebookCell('code', '', 'python');
          } else if (action === 'add-markdown') {
            createNotebookCell('markdown', '## Markdown 笔记\n在这里记录你的思考与观察。');
          } else if (action === 'reset-session') {
            resetNotebookSession();
          }
          nbSettingsPanel.classList.remove('is-visible');
          rerenderNotebook();
        });
      });
    }
  }

  function renderDetailSection(key, project = null) {
    const wrap = document.getElementById('detailContent');
    const videoArea = document.querySelector('.detail__video');
    
    // 获取当前项目（如果未传入）
    if (!project) {
      project = getCurrentProject();
    }
    
    // 从配置获取章节定义
    if (!window.ProjectStructureConfig) {
      console.warn(`[renderDetailSection] ProjectStructureConfig 未加载，使用默认渲染逻辑`);
      // 回退到旧的硬编码逻辑
      renderDetailSectionLegacy(key);
      return;
    }
    
    const sectionConfig = window.ProjectStructureConfig.getSection(key);
    if (!sectionConfig) {
      console.warn(`[renderDetailSection] 章节 "${key}" 未在配置中找到`);
      wrap.innerHTML = '<p>章节未找到</p>';
      return;
    }
    
    // 更新当前分区
    currentSection = key;
    
    // 处理视频区域显示/隐藏（基于配置类型）
    if (sectionConfig.type === 'quiz' || sectionConfig.type === 'comments' || sectionConfig.type === 'custom') {
      // custom类型（如小频道）也需要隐藏视频区域
      if (videoArea) videoArea.style.display = 'none';
    } else {
      if (videoArea) videoArea.style.display = '';
    }
    
    // 从项目数据获取内容，如果没有则使用默认内容
    let content = null;
    if (project?.detailContent?.[key]) {
      content = project.detailContent[key];
    } else {
      // 使用配置中的默认内容
      content = window.ProjectStructureConfig.getDefaultContent(key);
    }
    
    // 根据章节类型调用对应的渲染器
    const renderer = window.RendererRegistry?.[sectionConfig.type];
    if (renderer && typeof renderer === 'function') {
      try {
        renderer(key, content, project);
      } catch (error) {
        console.error(`[renderDetailSection] 渲染章节 "${key}" 时出错:`, error);
        wrap.innerHTML = `<p>渲染出错: ${error.message}</p>`;
      }
    } else {
      console.error(`[renderDetailSection] 未找到类型 "${sectionConfig.type}" 的渲染器`);
      // 回退到旧的硬编码逻辑
      renderDetailSectionLegacy(key);
    }
  }
  
  // 旧的渲染逻辑（作为回退）
  function renderDetailSectionLegacy(key) {
    const wrap = document.getElementById('detailContent');
    const videoArea = document.querySelector('.detail__video');
    
    currentSection = key;
    
    if (key === 'personalize' || key === 'comments') {
      if (videoArea) videoArea.style.display = 'none';
    } else {
      if (videoArea) videoArea.style.display = '';
    }
    
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
    } else if (key === 'channels') {
      renderChannelsSection(wrap);
    } else {
      // 恢复视频区域和标签页（其他分区）
      const videoArea = qs('.detail__video');
      const contentTabs = qs('.content-tabs');
      if (videoArea) videoArea.style.display = '';
      if (contentTabs) contentTabs.style.display = '';
      wrap.innerHTML = `<p>即将上线…</p>`;
    }
  }

  function renderPersonalizeSection(wrap, quizData = null) {
    // 个性化检验 - 如果没有传入quizData，使用默认题目
    if (!quizData || !Array.isArray(quizData) || quizData.length === 0) {
      // 使用默认题目（保持向后兼容）
      quizData = [
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
    }

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
      renderPersonalizeSection(wrap, quizData);
    });
  }

  function renderChannelsSection(wrap) {
    console.log('[renderChannelsSection] 开始渲染小频道界面');
    
    // 确保wrap存在
    if (!wrap) {
      console.error('[renderChannelsSection] wrap 元素未找到');
      wrap = document.getElementById('detailContent');
      if (!wrap) {
        console.error('[renderChannelsSection] detailContent 元素也未找到');
        return;
      }
    }
    
    // 隐藏视频区域和标签页
    const videoArea = qs('.detail__video');
    const contentTabs = qs('.content-tabs');
    if (videoArea) videoArea.style.display = 'none';
    if (contentTabs) contentTabs.style.display = 'none';
    
    // 获取当前项目ID
    const currentProjectId = window.currentProjectId || 'default';
    console.log('[renderChannelsSection] 当前项目ID:', currentProjectId);
    
    const projectOnboardingKey = `channels_onboarding_${currentProjectId}`;
    
    // 检查当前项目是否已完成引导流程
    const projectOnboarding = JSON.parse(localStorage.getItem(projectOnboardingKey) || 'null');
    
    if (!projectOnboarding || !projectOnboarding.completed) {
      console.log('[renderChannelsSection] 未完成引导流程，显示引导模态框');
      // 显示引导流程
      const onboardingModal = qs('#channelsOnboardingModal');
      if (onboardingModal) {
        onboardingModal.classList.add('active');
        initChannelsOnboarding(currentProjectId);
        // 同时显示主界面（即使未完成引导，也可以看到界面）
        renderChannelsMainInterface(wrap, currentProjectId);
      } else {
        console.warn('[renderChannelsSection] 引导模态框未找到，直接显示主界面');
        // 如果模态框不存在，直接显示主界面
        renderChannelsMainInterface(wrap, currentProjectId);
      }
    } else {
      console.log('[renderChannelsSection] 已完成引导流程，显示主界面');
      // 显示主界面
      renderChannelsMainInterface(wrap, currentProjectId);
    }
  }

  function initChannelsOnboarding(projectId) {
    let currentStep = 1;
    let teamName = '';
    let userName = 'mingxuan wang';
    let userAvatar = null;
    let inviteCode = '';
    
    // 获取当前登录用户信息
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
    if (currentUser && currentUser.username) {
      userName = currentUser.username;
    }

    // 步骤一：团队名称
    const step1Next = qs('#step1Next');
    const teamNameInput = qs('#teamNameInput');
    
    if (step1Next) {
      step1Next.addEventListener('click', () => {
        const name = teamNameInput?.value.trim();
        if (!name) {
          alert('请输入团队名称');
          return;
        }
        teamName = name;
        showStep(2);
        updateTeamNameDisplay(teamName);
      });
    }

    // 步骤二：姓名和头像
    const step2Next = qs('#step2Next');
    const userNameInput = qs('#userNameInput');
    const editPhotoBtn = qs('#editPhotoBtn');
    const avatarUpload = qs('#avatarUpload');
    const userAvatarEl = qs('#userAvatar');
    const avatarInitial = qs('#avatarInitial');

    if (step2Next) {
      step2Next.addEventListener('click', () => {
        const name = userNameInput?.value.trim();
        if (!name) {
          alert('请输入你的姓名');
          return;
        }
        userName = name;
        updateAvatarInitial(name);
        showStep(3);
      });
    }

    if (editPhotoBtn && avatarUpload) {
      editPhotoBtn.addEventListener('click', () => {
        avatarUpload.click();
      });
    }

    if (avatarUpload) {
      avatarUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = (event) => {
            userAvatar = event.target.result;
            if (userAvatarEl) {
              userAvatarEl.innerHTML = `<img src="${userAvatar}" alt="Avatar" />`;
            }
          };
          reader.readAsDataURL(file);
        }
      });
    }

    // 步骤三：邀请团队成员
    const step3Next = qs('#step3Next');
    const generateInviteCodeBtn = qs('#generateInviteCodeBtn');
    const copyInviteCodeBtn = qs('#copyInviteCodeBtn');
    const copyInviteLinkBtn = qs('#copyInviteLinkBtn');
    const skipStep3Btn = qs('#skipStep3Btn');
    const inviteCodeDisplay = qs('#inviteCodeDisplay');

    // generateInviteCodeBtn 的事件在 step3Next 部分处理

    if (copyInviteCodeBtn) {
      copyInviteCodeBtn.addEventListener('click', () => {
        if (inviteCodeDisplay) {
          inviteCodeDisplay.select();
          document.execCommand('copy');
          alert('邀请码已复制到剪贴板');
        }
      });
    }

    if (copyInviteLinkBtn) {
      copyInviteLinkBtn.addEventListener('click', () => {
        const inviteLink = `${window.location.origin}${window.location.pathname}#invite/${inviteCode || 'temp'}`;
        navigator.clipboard.writeText(inviteLink).then(() => {
          alert('邀请链接已复制到剪贴板');
        });
      });
    }

    if (skipStep3Btn) {
      skipStep3Btn.addEventListener('click', () => {
        showStep(4);
      });
    }

    if (step3Next) {
      // 初始状态：下一步按钮禁用
      step3Next.disabled = true;
      step3Next.style.opacity = '0.5';
      step3Next.style.cursor = 'not-allowed';

      const enableNext = () => {
        step3Next.disabled = false;
        step3Next.style.opacity = '1';
        step3Next.style.cursor = 'pointer';
      };

      // 监听邮箱输入或邀请码生成
      const inviteEmailsInput = qs('#inviteEmailsInput');
      if (inviteEmailsInput) {
        inviteEmailsInput.addEventListener('input', () => {
          if (inviteEmailsInput.value.trim() || inviteCode) {
            enableNext();
          } else {
            step3Next.disabled = true;
            step3Next.style.opacity = '0.5';
            step3Next.style.cursor = 'not-allowed';
          }
        });
      }

      // 生成邀请码后启用
      if (generateInviteCodeBtn) {
        generateInviteCodeBtn.addEventListener('click', () => {
          inviteCode = generateInviteCode();
          if (inviteCodeDisplay) {
            inviteCodeDisplay.value = inviteCode;
          }
          if (copyInviteCodeBtn) {
            copyInviteCodeBtn.style.display = 'inline-block';
          }
          enableNext();
        });
      }

      step3Next.addEventListener('click', () => {
        if (!step3Next.disabled) {
          showStep(4);
        }
      });
    }

    // 步骤四：完成
    const finishOnboardingBtn = qs('#finishOnboardingBtn');
    const closeOnboardingBtn = qs('#closeChannelsOnboarding');

    if (finishOnboardingBtn) {
      finishOnboardingBtn.addEventListener('click', () => {
        // 保存团队数据（全局）
        const teamData = {
          teamName: teamName,
          userName: userName,
          userAvatar: userAvatar,
          inviteCode: inviteCode,
          createdAt: new Date().toISOString()
        };
        localStorage.setItem('channels_team_data', JSON.stringify(teamData));
        
        // 按项目存储引导流程完成状态
        const projectOnboardingKey = `channels_onboarding_${projectId}`;
        const projectOnboarding = {
          completed: true,
          completedAt: new Date().toISOString(),
          projectId: projectId
        };
        localStorage.setItem(projectOnboardingKey, JSON.stringify(projectOnboarding));
        
        // 关闭模态框
        const modal = qs('#channelsOnboardingModal');
        if (modal) {
          modal.classList.remove('active');
        }
        
        // 重新渲染小频道界面
        const wrap = qs('#detailContent');
        if (wrap) {
          renderChannelsMainInterface(wrap, projectId);
        }
      });
    }

    if (closeOnboardingBtn) {
      closeOnboardingBtn.addEventListener('click', () => {
        const modal = qs('#channelsOnboardingModal');
        if (modal) {
          modal.classList.remove('active');
        }
      });
    }

    // 视频播放器已移除

    // 点击遮罩层关闭（仅在步骤1-3）
    const modal = qs('#channelsOnboardingModal');
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal || e.target.classList.contains('modal__overlay')) {
          if (currentStep < 4) {
            modal.classList.remove('active');
          }
        }
      });
    }

    function showStep(step) {
      for (let i = 1; i <= 4; i++) {
        const stepEl = qs(`#onboardingStep${i}`);
        if (stepEl) {
          stepEl.style.display = i === step ? 'flex' : 'none';
        }
      }
      currentStep = step;
    }

    function updateTeamNameDisplay(name) {
      const teamNameDisplay = qs('#teamNameDisplay');
      if (teamNameDisplay) {
        teamNameDisplay.textContent = name;
      }
    }

    function updateAvatarInitial(name) {
      const initial = name.charAt(0).toLowerCase();
      if (avatarInitial) {
        avatarInitial.textContent = initial;
      }
    }

    function generateInviteCode() {
      const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
      let code = '';
      for (let i = 0; i < 4; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      code += '-';
      for (let i = 0; i < 4; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      return code;
    }
  }

  function renderChannelsMainInterface(wrap, projectId) {
    console.log('[renderChannelsMainInterface] 开始渲染小频道主界面，项目ID:', projectId);
    
    if (!wrap) {
      console.error('[renderChannelsMainInterface] wrap 元素未找到');
      return;
    }
    
    const teamData = JSON.parse(localStorage.getItem('channels_team_data') || '{}');
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
    const currentUsername = currentUser ? currentUser.username : (teamData.userName || '你');
    
    // 获取当前项目的好友列表
    const friendsKey = `channels_friends_${projectId}`;
    const friends = JSON.parse(localStorage.getItem(friendsKey) || '[]');
    
    // 获取好友请求
    const friendRequestsKey = `channels_friend_requests_${projectId}`;
    const friendRequests = JSON.parse(localStorage.getItem(friendRequestsKey) || '[]');
    const pendingRequests = friendRequests.filter(req => req.to === currentUsername && req.status === 'pending');
    
    // 获取未读私信数量
    const unreadDMsKey = `channels_unread_dms_${projectId}`;
    const unreadDMs = JSON.parse(localStorage.getItem(unreadDMsKey) || '{}');
    const unreadCount = Object.values(unreadDMs).reduce((sum, count) => sum + count, 0);
    
    // 默认显示"新频道"的消息
    const channelName = '新频道';
    const messagesKey = `channels_messages_${projectId}_${channelName}`;
    const messages = JSON.parse(localStorage.getItem(messagesKey) || '[]');
    
    console.log('[renderChannelsMainInterface] 准备渲染HTML，消息数量:', messages.length);

    wrap.innerHTML = `
      <div class="channels-container">
        <!-- 左侧导航栏 -->
        <aside class="channels-sidebar">
          <div class="channels-sidebar-header">
            <div class="channels-workspace">${teamData.teamName ? teamData.teamName.charAt(0).toUpperCase() : '1'}</div>
          </div>
          <nav class="channels-nav">
            <button class="channels-nav-item is-active" data-nav="home">
              <svg viewBox="0 0 16 16" fill="none"><path d="M2 4L8 1L14 4V13C14 13.5304 13.7893 14.0391 13.4142 14.4142C13.0391 14.7893 12.5304 15 12 15H4C3.46957 15 2.96086 14.7893 2.58579 14.4142C2.21071 14.0391 2 13.5304 2 13V4Z" stroke="currentColor" stroke-width="1.5"/><path d="M6 15V8H10V15" stroke="currentColor" stroke-width="1.5"/></svg>
              <span>主页</span>
            </button>
            <button class="channels-nav-item" data-nav="messages">
              <svg viewBox="0 0 16 16" fill="none"><path d="M3 3h10v10H3z" stroke="currentColor" stroke-width="1.5"/><path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="1.5"/></svg>
              <span>私信</span>
              ${unreadCount > 0 ? `<span class="channels-nav-badge">${unreadCount}</span>` : ''}
            </button>
            <button class="channels-nav-item" data-nav="activity">
              <svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/><path d="M8 4v4l3 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
              <span>活动</span>
              ${pendingRequests.length > 0 ? `<span class="channels-nav-badge">${pendingRequests.length}</span>` : ''}
            </button>
            <button class="channels-nav-item" data-nav="files">
              <svg viewBox="0 0 16 16" fill="none"><path d="M8.5 2L14 7.5V13C14 13.2652 13.8946 13.5196 13.7071 13.7071C13.5196 13.8946 13.2652 14 13 14H3C2.73478 14 2.48043 13.8946 2.29289 13.7071C2.10536 13.5196 2 13.2652 2 13V3C2 2.73478 2.10536 2.48043 2.29289 2.29289C2.48043 2.10536 2.73478 2 3 2H8.5Z" stroke="currentColor" stroke-width="1.5"/></svg>
              <span>文件</span>
            </button>
          </nav>
          <div class="channels-section">
            <div class="channels-section-title">频道</div>
            <ul class="channels-list">
              <li class="channels-list-item is-active" data-channel="new">新频道</li>
              <li class="channels-list-item" data-channel="project">项目讨论</li>
              <li class="channels-list-item" data-channel="tech">技术交流</li>
            </ul>
          </div>
          <div class="channels-section">
            <div class="channels-section-title">话题标签</div>
            <div class="channels-tags" id="channelsTags" style="display: none;">
              <span class="channels-tag" data-tag="进度汇报">#进度汇报</span>
              <span class="channels-tag" data-tag="需求变更">#需求变更</span>
              <span class="channels-tag" data-tag="问题追踪">#问题追踪</span>
            </div>
          </div>
          <div class="channels-section">
            <div class="channels-section-title">
              好友
              <button class="btn btn--ghost btn--tiny" id="addFriendBtn" title="添加好友">+</button>
            </div>
            <ul class="channels-list" id="friendsList">
              ${friends.length > 0 ? friends.map(friend => `
                <li class="channels-list-item" data-friend="${friend.username}">
                  <span>${friend.username}</span>
                  ${friend.online ? '<span class="online-indicator" title="在线"></span>' : ''}
                </li>
              `).join('') : '<li class="channels-list-item channels-list-empty">暂无好友</li>'}
            </ul>
          </div>
        </aside>

        <!-- 主内容区 -->
        <main class="channels-main">
          <div class="channels-header">
            <div class="channels-header-left">
              <h2 class="channels-header-title">新频道</h2>
              <button class="btn btn--ghost btn--small">添加成员</button>
            </div>
            <div class="channels-header-actions">
              <label for="channelsSearchInput" class="sr-only">搜索频道</label>
              <input type="search" id="channelsSearchInput" name="channelsSearch" class="channels-search" placeholder="搜索" autocomplete="off" />
            </div>
          </div>

          <div class="channels-messages" id="channelsMessages">
            ${renderChannelMessages(channelName, messages, projectId)}
          </div>

          <div class="channels-input-area">
            <div class="channels-input-toolbar">
              <button class="channels-toolbar-btn" title="粗体">
                <svg viewBox="0 0 16 16" fill="none"><path d="M4 3h5a3 3 0 0 1 0 6H4V3zM4 9h4a2 2 0 0 1 0 4H4V9z" stroke="currentColor" stroke-width="1.5"/></svg>
              </button>
              <button class="channels-toolbar-btn" title="斜体">
                <svg viewBox="0 0 16 16" fill="none"><path d="M6 3h4M5 13h4M7 3l-2 10" stroke="currentColor" stroke-width="1.5"/></svg>
              </button>
              <button class="channels-toolbar-btn" title="代码块">
                <svg viewBox="0 0 16 16" fill="none"><path d="M6 4L2 8l4 4M10 4l4 4-4 4" stroke="currentColor" stroke-width="1.5"/></svg>
              </button>
              <div class="channels-tags-input" id="channelsTagsInput" style="display: none;">
                <span class="channels-tag channels-tag--clickable" data-tag="进度汇报">#进度汇报</span>
                <span class="channels-tag channels-tag--clickable" data-tag="需求变更">#需求变更</span>
                <span class="channels-tag channels-tag--clickable" data-tag="问题追踪">#问题追踪</span>
              </div>
            </div>
            <div class="channels-input-wrapper">
              <label for="channelsMessageInput" class="sr-only">输入消息</label>
              <textarea class="channels-input" id="channelsMessageInput" name="channelMessage" placeholder="消息 #新频道" autocomplete="off"></textarea>
              <button class="channels-send-btn" id="channelsSendBtn">
                <svg viewBox="0 0 16 16" fill="none"><path d="M4 12L12 4M6 4h6v6" stroke="currentColor" stroke-width="1.6"/></svg>
              </button>
            </div>
          </div>
        </main>
      </div>
    `;

    // 绑定发送消息事件
    const sendBtn = wrap.querySelector('#channelsSendBtn');
    const messageInput = wrap.querySelector('#channelsMessageInput');

    if (sendBtn && messageInput) {
      const sendMessage = () => {
        const text = messageInput.value.trim();
        if (!text) return;
        
        // 获取当前选中的频道
        const activeChannel = wrap.querySelector('.channels-list-item.is-active');
        const channelName = activeChannel ? activeChannel.textContent.trim() : '新频道';
        
        // 按项目和频道存储消息
        const messagesKey = `channels_messages_${projectId}_${channelName}`;
        const messages = JSON.parse(localStorage.getItem(messagesKey) || '[]');
        
        const newMessage = {
          id: Date.now(),
          author: currentUsername,
          text: text,
          time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
        };

        messages.push(newMessage);
        localStorage.setItem(messagesKey, JSON.stringify(messages));

        messageInput.value = '';
        
        // 更新当前频道消息显示
        switchChannel(channelName, wrap, projectId);
      };

      sendBtn.addEventListener('click', sendMessage);
      messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendMessage();
        }
      });
    }

    // 绑定导航项点击事件（防止跳转）
    const navItems = wrap.querySelectorAll('.channels-nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        // 移除所有活动状态
        navItems.forEach(nav => nav.classList.remove('is-active'));
        // 添加当前活动状态
        item.classList.add('is-active');
        
        const navType = item.dataset.nav;
        switchChannelsView(navType, wrap, projectId);
      });
    });

    // 绑定频道列表点击事件
    const channelItems = wrap.querySelectorAll('.channels-list-item');
    channelItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        // 移除所有活动状态
        channelItems.forEach(ch => ch.classList.remove('is-active'));
        // 添加当前活动状态
        item.classList.add('is-active');
        
        // 确保主页视图处于活动状态
        const homeNav = wrap.querySelector('.channels-nav-item[data-nav="home"]');
        if (homeNav) {
          wrap.querySelectorAll('.channels-nav-item').forEach(nav => nav.classList.remove('is-active'));
          homeNav.classList.add('is-active');
        }
        
        const channelName = item.textContent.trim();
        switchChannel(channelName, wrap, projectId);
        
        // 显示/隐藏话题标签输入（仅项目讨论频道）
        const tagsInput = wrap.querySelector('#channelsTagsInput');
        if (tagsInput) {
          tagsInput.style.display = channelName === '项目讨论' ? 'flex' : 'none';
        }
      });
    });
    
    // 绑定话题标签点击事件（在输入框中）
    const tagButtons = wrap.querySelectorAll('.channels-tag--clickable');
    tagButtons.forEach(tag => {
      tag.addEventListener('click', () => {
        const tagText = tag.dataset.tag;
        const messageInput = wrap.querySelector('#channelsMessageInput');
        if (messageInput) {
          const currentText = messageInput.value.trim();
          const tagWithSpace = `#${tagText} `;
          if (!currentText.includes(tagWithSpace)) {
            messageInput.value = currentText ? `${currentText} ${tagWithSpace}` : tagWithSpace;
            messageInput.focus();
          }
        }
      });
    });

    // 绑定好友列表点击事件
    const friendItems = wrap.querySelectorAll('[data-friend]');
    friendItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const friendName = item.dataset.friend;
        // 切换到私信视图并打开与好友的对话
        const messagesNav = wrap.querySelector('.channels-nav-item[data-nav="messages"]');
        if (messagesNav) {
          wrap.querySelectorAll('.channels-nav-item').forEach(nav => nav.classList.remove('is-active'));
          messagesNav.classList.add('is-active');
          switchChannelsView('messages', wrap, projectId, friendName);
        }
      });
    });

    // 绑定添加好友按钮
    const addFriendBtn = wrap.querySelector('#addFriendBtn');
    if (addFriendBtn) {
      addFriendBtn.addEventListener('click', () => {
        showAddFriendModal(projectId, wrap);
      });
    }
  }

  function switchChannelsView(viewType, wrap, projectId, friendName) {
    // 切换不同的视图（主页、私信、活动、文件）
    const messagesArea = wrap.querySelector('#channelsMessages');
    if (!messagesArea) return;
    
    projectId = projectId || window.currentProjectId || 'default';

    switch(viewType) {
      case 'home':
        // 显示当前选中频道的消息
        const activeChannel = wrap.querySelector('.channels-list-item.is-active');
        const currentChannelName = activeChannel ? activeChannel.textContent.trim() : '新频道';
        const channelMessages = JSON.parse(localStorage.getItem(`channels_messages_${projectId}_${currentChannelName}`) || '[]');
        messagesArea.innerHTML = channelMessages.length > 0 ? channelMessages.map(msg => `
          <div class="channels-message">
            <div class="channels-message-avatar">${msg.author.charAt(0).toUpperCase()}</div>
            <div class="channels-message-content">
              <div class="channels-message-header">
                <span class="channels-message-author">${msg.author}</span>
                <span class="channels-message-time">${msg.time}</span>
              </div>
              <p class="channels-message-text">${msg.text}</p>
            </div>
          </div>
        `).join('') : `
          <div style="text-align: center; padding: 60px 20px; color: var(--text-2);">
            <p style="font-size: 18px; margin-bottom: 8px;">欢迎来到你的第一个频道！</p>
            <p style="font-size: 14px;">开始发送消息，与团队成员交流吧。</p>
          </div>
        `;
        break;
      case 'messages':
        // 显示私信列表或与特定好友的对话
        const friendName = arguments[2] || null;
        if (friendName) {
          renderDirectMessage(wrap, projectId, friendName);
        } else {
          renderDirectMessagesList(wrap, projectId);
        }
        break;
      case 'activity':
        renderActivityView(wrap, projectId);
        break;
      case 'files':
        messagesArea.innerHTML = `
          <div style="text-align: center; padding: 60px 20px; color: var(--text-2);">
            <p style="font-size: 18px; margin-bottom: 8px;">文件管理</p>
            <p style="font-size: 14px;">查看和下载团队共享的文件。</p>
          </div>
        `;
        break;
    }
  }

  // 渲染频道消息（包含置顶消息和欢迎消息）
  function renderChannelMessages(channelName, messages, projectId) {
    let html = '';
    
    // 如果是"项目讨论"频道，显示置顶消息和频道信息
    if (channelName === '项目讨论') {
      html += `
        <div class="channels-pinned-message">
          <div class="channels-pinned-header">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 1L10 6L15 6L11 9L12 15L8 12L4 15L5 9L1 6L6 6L8 1Z" fill="currentColor"/></svg>
            <span>频道信息</span>
          </div>
          <div class="channels-channel-info">
            <div class="channel-intro">
              <strong>频道简介：</strong>
              <p>用于团队成员共享项目进展、协调任务与解决问题的主要交流区。</p>
            </div>
            <div class="channel-rules">
              <strong>频道规则：</strong>
              <ol>
                <li>发言前请明确主题并@相关成员</li>
                <li>汇报进展时建议附带最新任务状态或截图</li>
                <li>讨论结束请总结结论并标记负责人</li>
              </ol>
            </div>
            <div class="channel-pinned">
              <strong>📌【讨论规范】</strong>
              <ul>
                <li>每周一上午更新项目进展</li>
                <li>讨论完毕请使用 ✅ 表示结论已确定</li>
                <li>所有问题需在24小时内回复</li>
              </ul>
              <div class="channel-template">
                <strong>模板：</strong>
                <pre>【任务】xxx
【进展】xxx
【待解决】xxx</pre>
              </div>
            </div>
            <div class="channel-tags-info">
              <strong>话题标签：</strong>
              <div class="channels-tags-inline">
                <span class="channels-tag">#进度汇报</span>
                <span class="channels-tag">#需求变更</span>
                <span class="channels-tag">#问题追踪</span>
              </div>
            </div>
          </div>
        </div>
      `;
      
      // 检查是否已有欢迎消息，如果没有则添加
      const welcomeMessageKey = `channels_welcome_${projectId}_${channelName}`;
      const hasWelcomeMessage = localStorage.getItem(welcomeMessageKey);
      
      if (!hasWelcomeMessage && messages.length === 0) {
        const welcomeMessage = {
          id: Date.now() - 1000, // 确保在置顶消息之后
          author: '系统',
          text: '👋 欢迎加入【项目讨论】频道！\n\n请先阅读置顶规则，并在首次发言时介绍你当前负责的模块。让我们一起推动项目顺利进行！',
          time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
          isSystem: true
        };
        messages.unshift(welcomeMessage);
        const messagesKey = `channels_messages_${projectId}_${channelName}`;
        localStorage.setItem(messagesKey, JSON.stringify(messages));
        localStorage.setItem(welcomeMessageKey, 'true');
      }
    }
    
    // 渲染普通消息
    if (messages.length > 0) {
      html += messages.map(msg => {
        const isSystem = msg.isSystem || msg.author === '系统';
        return `
          <div class="channels-message ${isSystem ? 'channels-message--system' : ''}">
            <div class="channels-message-avatar">${msg.author.charAt(0).toUpperCase()}</div>
            <div class="channels-message-content">
              <div class="channels-message-header">
                <span class="channels-message-author">${msg.author}</span>
                <span class="channels-message-time">${msg.time}</span>
              </div>
              <p class="channels-message-text">${msg.text.replace(/\n/g, '<br>')}</p>
            </div>
          </div>
        `;
      }).join('');
    } else if (channelName !== '项目讨论') {
      html += `
        <div style="text-align: center; padding: 60px 20px; color: var(--text-2);">
          <p style="font-size: 18px; margin-bottom: 8px;">欢迎来到 ${channelName}！</p>
          <p style="font-size: 14px;">开始发送消息，与团队成员交流吧。</p>
        </div>
      `;
    }
    
    return html;
  }

  function switchChannel(channelName, wrap, projectId) {
    // 切换频道
    const headerTitle = wrap.querySelector('.channels-header-title');
    const messageInput = wrap.querySelector('#channelsMessageInput');
    const tagsContainer = wrap.querySelector('#channelsTags');
    
    if (headerTitle) {
      headerTitle.innerHTML = `<span>${channelName}</span>`;
    }
    
    if (messageInput) {
      messageInput.placeholder = `消息 ${channelName}`;
    }

    // 显示/隐藏话题标签（仅项目讨论频道显示）
    if (tagsContainer) {
      tagsContainer.style.display = channelName === '项目讨论' ? 'flex' : 'none';
    }

    // 加载该频道的消息
    const messagesKey = `channels_messages_${projectId}_${channelName}`;
    const messages = JSON.parse(localStorage.getItem(messagesKey) || '[]');
    const messagesArea = wrap.querySelector('#channelsMessages');
    
    if (messagesArea) {
      messagesArea.innerHTML = renderChannelMessages(channelName, messages, projectId);
      
      // 滚动到底部
      messagesArea.scrollTop = messagesArea.scrollHeight;
    }
  }

  // 显示添加好友模态框
  function showAddFriendModal(projectId, wrap) {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.innerHTML = `
      <div class="modal__overlay"></div>
      <div class="modal__content">
        <button class="modal__close" id="closeAddFriendModal">×</button>
        <h2 class="modal__title">添加好友</h2>
        <div style="padding: 20px;">
          <label for="friendUsernameInput" class="form__label">用户名</label>
          <input type="text" id="friendUsernameInput" class="input input--full" placeholder="输入要添加的好友用户名" autocomplete="off" />
          <div style="margin-top: 16px; display: flex; gap: 8px;">
            <button class="btn btn--primary" id="sendFriendRequestBtn">发送好友请求</button>
            <button class="btn btn--ghost" id="cancelAddFriendBtn">取消</button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    const closeBtn = modal.querySelector('#closeAddFriendModal');
    const cancelBtn = modal.querySelector('#cancelAddFriendBtn');
    const sendBtn = modal.querySelector('#sendFriendRequestBtn');
    const usernameInput = modal.querySelector('#friendUsernameInput');

    const closeModal = () => {
      document.body.removeChild(modal);
    };

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);
    modal.querySelector('.modal__overlay').addEventListener('click', closeModal);

    sendBtn.addEventListener('click', () => {
      const friendUsername = usernameInput.value.trim();
      if (!friendUsername) {
        alert('请输入用户名');
        return;
      }

      const currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
      const currentUsername = currentUser ? currentUser.username : '你';

      if (friendUsername === currentUsername) {
        alert('不能添加自己为好友');
        return;
      }

      // 检查是否已经是好友
      const friendsKey = `channels_friends_${projectId}`;
      const friends = JSON.parse(localStorage.getItem(friendsKey) || '[]');
      if (friends.find(f => f.username === friendUsername)) {
        alert('该用户已经是你的好友');
        closeModal();
        return;
      }

      // 发送好友请求
      const friendRequestsKey = `channels_friend_requests_${projectId}`;
      const friendRequests = JSON.parse(localStorage.getItem(friendRequestsKey) || '[]');
      
      // 检查是否已经发送过请求
      if (friendRequests.find(req => req.from === currentUsername && req.to === friendUsername && req.status === 'pending')) {
        alert('已经发送过好友请求，请等待对方回复');
        closeModal();
        return;
      }

      const newRequest = {
        id: Date.now(),
        from: currentUsername,
        to: friendUsername,
        status: 'pending',
        createdAt: new Date().toISOString()
      };

      friendRequests.push(newRequest);
      localStorage.setItem(friendRequestsKey, JSON.stringify(friendRequests));

      alert('好友请求已发送！');
      closeModal();
      
      // 重新渲染界面以更新活动徽章
      renderChannelsMainInterface(wrap, projectId);
    });
  }

  // 渲染私信列表
  function renderDirectMessagesList(wrap, projectId) {
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
    const currentUsername = currentUser ? currentUser.username : '你';
    const friendsKey = `channels_friends_${projectId}`;
    const friends = JSON.parse(localStorage.getItem(friendsKey) || '[]');
    
    const messagesArea = wrap.querySelector('#channelsMessages');
    const headerTitle = wrap.querySelector('.channels-header-title');
    
    if (headerTitle) {
      headerTitle.innerHTML = '<span>私信</span>';
    }

    if (messagesArea) {
      if (friends.length === 0) {
        messagesArea.innerHTML = `
          <div style="text-align: center; padding: 60px 20px; color: var(--text-2);">
            <p style="font-size: 18px; margin-bottom: 8px;">暂无好友</p>
            <p style="font-size: 14px;">添加好友后可以开始私信对话。</p>
          </div>
        `;
      } else {
        messagesArea.innerHTML = friends.map(friend => {
          // 获取最后一条消息
          const dmKey = `channels_dm_${projectId}_${currentUsername}_${friend.username}`;
          const messages = JSON.parse(localStorage.getItem(dmKey) || '[]');
          const lastMessage = messages.length > 0 ? messages[messages.length - 1] : null;
          
          return `
            <div class="channels-dm-item" data-friend="${friend.username}" style="padding: 16px; border-bottom: 1px solid var(--border); cursor: pointer; display: flex; align-items: center; gap: 12px;">
              <div class="channels-message-avatar">${friend.username.charAt(0).toUpperCase()}</div>
              <div style="flex: 1;">
                <div style="font-weight: 600; margin-bottom: 4px;">${friend.username}</div>
                ${lastMessage ? `<div style="font-size: 13px; color: var(--text-2);">${lastMessage.text}</div>` : '<div style="font-size: 13px; color: var(--text-2);">暂无消息</div>'}
              </div>
              ${lastMessage ? `<div style="font-size: 12px; color: var(--text-2);">${lastMessage.time}</div>` : ''}
            </div>
          `;
        }).join('');

        // 绑定点击事件
        const dmItems = messagesArea.querySelectorAll('.channels-dm-item');
        dmItems.forEach(item => {
          item.addEventListener('click', () => {
            const friendName = item.dataset.friend;
            renderDirectMessage(wrap, projectId, friendName);
          });
        });
      }
    }
  }

  // 渲染与好友的私信对话
  function renderDirectMessage(wrap, projectId, friendName) {
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
    const currentUsername = currentUser ? currentUser.username : '你';
    
    // 获取私信消息（双向存储）
    const dmKey1 = `channels_dm_${projectId}_${currentUsername}_${friendName}`;
    const dmKey2 = `channels_dm_${projectId}_${friendName}_${currentUsername}`;
    const messages1 = JSON.parse(localStorage.getItem(dmKey1) || '[]');
    const messages2 = JSON.parse(localStorage.getItem(dmKey2) || '[]');
    
    // 合并消息并按时间排序
    const allMessages = [...messages1, ...messages2].sort((a, b) => a.id - b.id);
    
    const messagesArea = wrap.querySelector('#channelsMessages');
    const headerTitle = wrap.querySelector('.channels-header-title');
    const messageInput = wrap.querySelector('#channelsMessageInput');
    
    if (headerTitle) {
      headerTitle.innerHTML = `<span>与 ${friendName} 的对话</span>`;
    }
    
    if (messageInput) {
      messageInput.placeholder = `发送私信给 ${friendName}...`;
    }

    if (messagesArea) {
      messagesArea.innerHTML = allMessages.length > 0 ? allMessages.map(msg => {
        const isMe = msg.from === currentUsername;
        return `
          <div class="channels-message" style="display: flex; ${isMe ? 'flex-direction: row-reverse;' : ''} margin-bottom: 16px;">
            <div class="channels-message-avatar">${msg.from.charAt(0).toUpperCase()}</div>
            <div class="channels-message-content" style="${isMe ? 'background: var(--brand); color: white;' : ''}">
              <div class="channels-message-header">
                <span class="channels-message-author">${msg.from}</span>
                <span class="channels-message-time">${msg.time}</span>
              </div>
              <p class="channels-message-text">${msg.text}</p>
            </div>
          </div>
        `;
      }).join('') : `
        <div style="text-align: center; padding: 60px 20px; color: var(--text-2);">
          <p style="font-size: 18px; margin-bottom: 8px;">开始与 ${friendName} 的对话</p>
          <p style="font-size: 14px;">发送第一条消息开始聊天吧。</p>
        </div>
      `;
      
      messagesArea.scrollTop = messagesArea.scrollHeight;
    }

    // 更新发送消息功能
    const sendBtn = wrap.querySelector('#channelsSendBtn');
    const input = wrap.querySelector('#channelsMessageInput');
    
    if (sendBtn && input) {
      // 移除旧的事件监听器（通过克隆节点）
      const newSendBtn = sendBtn.cloneNode(true);
      sendBtn.parentNode.replaceChild(newSendBtn, sendBtn);
      const newInput = input.cloneNode(true);
      input.parentNode.replaceChild(newInput, input);

      const sendDirectMessage = () => {
        const text = newInput.value.trim();
        if (!text) return;

        const newMessage = {
          id: Date.now(),
          from: currentUsername,
          to: friendName,
          text: text,
          time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
        };

        // 存储到当前用户的私信记录
        const messages = JSON.parse(localStorage.getItem(dmKey1) || '[]');
        messages.push(newMessage);
        localStorage.setItem(dmKey1, JSON.stringify(messages));

        newInput.value = '';
        renderDirectMessage(wrap, projectId, friendName);
      };

      newSendBtn.addEventListener('click', sendDirectMessage);
      newInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendDirectMessage();
        }
      });
    }
  }

  // 渲染活动动态视图（好友请求）
  function renderActivityView(wrap, projectId) {
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
    const currentUsername = currentUser ? currentUser.username : '你';
    
    const friendRequestsKey = `channels_friend_requests_${projectId}`;
    const friendRequests = JSON.parse(localStorage.getItem(friendRequestsKey) || '[]');
    const pendingRequests = friendRequests.filter(req => req.to === currentUsername && req.status === 'pending');
    
    const messagesArea = wrap.querySelector('#channelsMessages');
    const headerTitle = wrap.querySelector('.channels-header-title');
    
    if (headerTitle) {
      headerTitle.innerHTML = '<span>活动动态</span>';
    }

    if (messagesArea) {
      if (pendingRequests.length === 0) {
        messagesArea.innerHTML = `
          <div style="text-align: center; padding: 60px 20px; color: var(--text-2);">
            <p style="font-size: 18px; margin-bottom: 8px;">暂无待处理的好友请求</p>
            <p style="font-size: 14px;">当有人向你发送好友请求时，会在这里显示。</p>
          </div>
        `;
      } else {
        messagesArea.innerHTML = pendingRequests.map(req => `
          <div class="activity-item" data-request-id="${req.id}" style="padding: 20px; border-bottom: 1px solid var(--border);">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
              <div class="channels-message-avatar">${req.from.charAt(0).toUpperCase()}</div>
              <div style="flex: 1;">
                <div style="font-weight: 600; margin-bottom: 4px;">${req.from}</div>
                <div style="font-size: 13px; color: var(--text-2);">想要添加你为好友</div>
              </div>
              <div style="font-size: 12px; color: var(--text-2);">${new Date(req.createdAt).toLocaleString('zh-CN')}</div>
            </div>
            <div style="display: flex; gap: 8px;">
              <button class="btn btn--primary btn--small accept-friend-btn" data-request-id="${req.id}">接受</button>
              <button class="btn btn--ghost btn--small reject-friend-btn" data-request-id="${req.id}">拒绝</button>
            </div>
          </div>
        `).join('');

        // 绑定接受/拒绝按钮
        const acceptBtns = messagesArea.querySelectorAll('.accept-friend-btn');
        const rejectBtns = messagesArea.querySelectorAll('.reject-friend-btn');

        acceptBtns.forEach(btn => {
          btn.addEventListener('click', () => {
            const requestId = parseInt(btn.dataset.requestId);
            const request = friendRequests.find(req => req.id === requestId);
            if (request) {
              // 更新请求状态
              request.status = 'accepted';
              localStorage.setItem(friendRequestsKey, JSON.stringify(friendRequests));

              // 添加到好友列表
              const friendsKey = `channels_friends_${projectId}`;
              const friends = JSON.parse(localStorage.getItem(friendsKey) || '[]');
              if (!friends.find(f => f.username === request.from)) {
                friends.push({
                  username: request.from,
                  addedAt: new Date().toISOString(),
                  online: false
                });
                localStorage.setItem(friendsKey, JSON.stringify(friends));
              }

              // 同时将对方添加到自己的好友列表（双向）
              const otherUserFriendsKey = `channels_friends_${projectId}`;
              // 注意：这里简化处理，实际应该为对方用户也添加好友关系
              
              alert('已接受好友请求！');
              renderActivityView(wrap, projectId);
              // 重新渲染主界面以更新好友列表
              renderChannelsMainInterface(wrap, projectId);
            }
          });
        });

        rejectBtns.forEach(btn => {
          btn.addEventListener('click', () => {
            const requestId = parseInt(btn.dataset.requestId);
            const request = friendRequests.find(req => req.id === requestId);
            if (request) {
              // 更新请求状态
              request.status = 'rejected';
              localStorage.setItem(friendRequestsKey, JSON.stringify(friendRequests));
              
              alert('已拒绝好友请求');
              renderActivityView(wrap, projectId);
            }
          });
        });
      }
    }
  }

  function renderCommentsSection(wrap, initialComments = null) {
    // 留言区 - 类似微信公众号评论区
    // 使用项目ID作为存储键，支持多项目独立留言
    const projectId = window.currentProjectId || 'default';
    const storageKey = `comments_${projectId}`;
    
    // 初始化留言数据（每次渲染时重新加载，支持项目切换）
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        window.commentsData = JSON.parse(stored);
      } else if (initialComments && Array.isArray(initialComments) && initialComments.length > 0) {
        window.commentsData = initialComments;
        // 保存初始留言到localStorage
        localStorage.setItem(storageKey, JSON.stringify(initialComments));
      } else {
        // 使用默认留言（保持向后兼容）
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
        // 保存默认留言到localStorage
        localStorage.setItem(storageKey, JSON.stringify(window.commentsData));
      }
    } catch (e) {
      console.error('[renderCommentsSection] 初始化留言数据失败:', e);
      window.commentsData = [];
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
            <label for="newCommentInput" class="sr-only">写下你的想法</label>
            <textarea class="comment-input" id="newCommentInput" name="newComment" placeholder="写下你的想法..." autocomplete="off"></textarea>
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
                      <label for="replyInput_${comment.id}" class="sr-only">写下你的回复</label>
                      <input type="text" id="replyInput_${comment.id}" name="replyText" class="reply-input" placeholder="写下你的回复..." autocomplete="off" />
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
      
      // 保存到localStorage（使用项目ID）
      const projectId = window.currentProjectId || 'default';
      const storageKey = `comments_${projectId}`;
      try {
        localStorage.setItem(storageKey, JSON.stringify(commentsData));
      } catch (e) {
        console.error('[renderCommentsSection] 保存留言失败:', e);
      }
      
      renderCommentsSection(wrap, initialComments);
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
          
          // 保存到localStorage
          const projectId = window.currentProjectId || 'default';
          const storageKey = `comments_${projectId}`;
          try {
            localStorage.setItem(storageKey, JSON.stringify(commentsData));
          } catch (e) {
            console.error('[renderCommentsSection] 保存点赞状态失败:', e);
          }
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
          const newReply = {
            id: Date.now(),
            author: "你",
            avatar: "👤",
            content: content,
            time: "刚刚",
            isAuthor: false
          };
          
          comment.replies.push(newReply);
          
          // 保存到localStorage
          const projectId = window.currentProjectId || 'default';
          const storageKey = `comments_${projectId}`;
          try {
            localStorage.setItem(storageKey, JSON.stringify(commentsData));
          } catch (e) {
            console.error('[renderCommentsSection] 保存回复失败:', e);
          }
          
          replyInput.value = '';
          replyArea.style.display = 'none';
          renderCommentsSection(wrap, initialComments);
        }
      });
    });
  }

  function switchView(view) {
    // 隐藏所有视图
    if (homeView) homeView.classList.remove('active');
    if (detailView) detailView.classList.remove('active');
    if (createViewGlobal) createViewGlobal.classList.remove('active');
    
    // 显示目标视图
    if (view === 'home' && homeView) {
      homeView.classList.add('active');
    } else if (view === 'detail' && detailView) {
      detailView.classList.add('active');
    } else if (view === 'create' && createViewGlobal) {
      createViewGlobal.classList.add('active');
    }
  }
  
  // 暴露到全局（供模块使用）
  window.switchView = switchView;
  window.renderChannelsSection = renderChannelsSection;

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
          <label for="loginUsername" class="form__label">用户名</label>
          <input type="text" id="loginUsername" name="username" class="input input--full" placeholder="请输入用户名" autocomplete="username" required />
        </div>
        <div class="form__group">
          <label for="loginPassword" class="form__label">密码</label>
          <input type="password" id="loginPassword" name="password" class="input input--full" placeholder="请输入密码" autocomplete="current-password" required />
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

  // 角色选择登录（测试模式：直接登录）
  roleCards.forEach(card => {
    card.addEventListener('click', () => {
      const role = card.getAttribute('data-role');
      const roleNames = {
        'enterprise': '企业用户',
        'teacher': '教师用户',
        'user': '普通用户',
        'admin': '管理员'
      };
      
      // 测试模式：直接登录，无需注册
      const username = roleNames[role] || role;
      handleLogin(role, username);
      
      if (loginModal) loginModal.classList.remove('active');
      
      console.log(`[登录] 角色: ${role}, 用户名: ${username}`);
    });
  });

  function handleLogin(role, username) {
    currentUserRole = role;
    window.currentUserRole = role;  // 同步到全局
    const roleNames = {
      'enterprise': '企业',
      'teacher': '高校教师',
      'user': '普通使用者',
      'admin': '管理员'
    };

    if (currentRoleEl) {
      currentRoleEl.textContent = roleNames[role] || role;
    }

    if (featureBar) {
      featureBar.style.display = 'block';
      document.body.classList.add('has-feature-bar');
    }

    // 获取审核按钮
    const adminReviewBtn = qs('#adminReviewBtn');

    // 根据角色显示/隐藏功能按钮
      if (role === 'enterprise' || role === 'teacher') {
      // 企业和教师：显示出题和上传按钮
      if (createProblemBtn) createProblemBtn.style.display = 'inline-block';
      if (uploadDataBtn) uploadDataBtn.style.display = 'inline-block';
      if (adminReviewBtn) adminReviewBtn.style.display = 'none';
    } else if (role === 'admin') {
      // 管理员：显示所有按钮
      if (createProblemBtn) createProblemBtn.style.display = 'inline-block';
      if (uploadDataBtn) uploadDataBtn.style.display = 'inline-block';
      if (adminReviewBtn) adminReviewBtn.style.display = 'inline-block';
      } else {
      // 普通用户：隐藏所有按钮
      if (createProblemBtn) createProblemBtn.style.display = 'none';
      if (uploadDataBtn) uploadDataBtn.style.display = 'none';
      if (adminReviewBtn) adminReviewBtn.style.display = 'none';
    }

    // 更新侧边栏个人中心信息
    const profileSubs = qsa('.profile__sub');
    profileSubs.forEach(el => {
      el.textContent = `已登录 · ${roleNames[role]} · ${username}`;
    });
  }

  if (createProblemBtn) {
    createProblemBtn.addEventListener('click', () => {
      // 检查权限
      if (currentUserRole === 'enterprise' || currentUserRole === 'teacher') {
        // 跳转到出题页面
        history.pushState({ view: 'create' }, '', '#create');
        switchView('create');
        // 重置表单
        const form = qs('#createProblemForm');
        if (form) form.reset();
      } else {
        alert('您没有出题权限，只有企业或高校教师可以出题。');
      }
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

  // 侧边栏切换功能
  const sidebarToggle = document.getElementById('sidebarToggle');
  const toggleIcon = document.getElementById('toggleIcon');
  let sidebarCollapsed = false;
  
  if (sidebarToggle && toggleIcon) {
    sidebarToggle.addEventListener('click', () => {
      sidebarCollapsed = !sidebarCollapsed;
      detailView.classList.toggle('sidebar-collapsed', sidebarCollapsed);
      toggleIcon.textContent = sidebarCollapsed ? '»' : '«';
    });
  }

  // Agent面板切换功能
  const agentToggle = document.getElementById('agentToggle');
  const agentToggleIcon = document.getElementById('agentToggleIcon');
  let agentCollapsed = false;
  
  if (agentToggle && agentToggleIcon) {
    agentToggle.addEventListener('click', () => {
      agentCollapsed = !agentCollapsed;
      detailView.classList.toggle('agent-collapsed', agentCollapsed);
      agentToggleIcon.textContent = agentCollapsed ? '«' : '»';
    });
  }

  // 视频区域切换功能
  const videoToggle = document.getElementById('videoToggle');
  const videoToggleIcon = document.getElementById('videoToggleIcon');
  const videoArea = document.querySelector('.detail__video');
  let videoCollapsed = false;
  
  if (videoToggle && videoToggleIcon && videoArea) {
    videoToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      videoCollapsed = !videoCollapsed;
      videoArea.classList.toggle('collapsed', videoCollapsed);
      videoToggleIcon.textContent = videoCollapsed ? '▼' : '▲';
      videoToggle.setAttribute('title', videoCollapsed ? '展开视频' : '收缩视频');
    });
  }

  // 内容区标签页切换
  const contentTabs = qsa('.content-tab');
  const tabContentAreas = qsa('.tab-content-area');
  
  contentTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetTab = tab.dataset.tab;
      
      // 切换标签激活状态
      contentTabs.forEach(t => t.classList.remove('is-active'));
      tab.classList.add('is-active');
      
      // 切换内容区显示
      tabContentAreas.forEach(area => {
        if (area.id === targetTab + 'Tab') {
          area.classList.add('is-active');
        } else {
          area.classList.remove('is-active');
        }
      });
      
      // 如果切换到代码运行页面，重置视频区域状态
      if (targetTab === 'run' && videoArea && videoCollapsed) {
        videoCollapsed = false;
        videoArea.classList.remove('collapsed');
        if (videoToggleIcon) videoToggleIcon.textContent = '▲';
      }
    });
  });

  // 代码运行功能
  const runAllCodeBtn = qs('#runAllCode');
  const clearOutputBtn = qs('#clearOutput');
  const codeRunnerContent = qs('#codeRunnerContent');

  if (runAllCodeBtn) {
    runAllCodeBtn.addEventListener('click', async () => {
      const originalText = runAllCodeBtn.textContent;
      runAllCodeBtn.disabled = true;
      runAllCodeBtn.textContent = '运行中...';
      try {
        await runAllCodeCells();
      } finally {
        runAllCodeBtn.disabled = false;
        runAllCodeBtn.textContent = originalText;
      }
    });
  }

  if (clearOutputBtn) {
    clearOutputBtn.addEventListener('click', () => {
      if (codeRunnerContent) {
        codeRunnerContent.innerHTML = `
          <div class="runner-placeholder">
            <p>✨ 在这里可以运行您在编辑视图中编写的所有代码</p>
            <p>点击"运行所有"按钮开始执行</p>
          </div>
        `;
      }
    });
  }

  async function runAllCodeCells() {
    if (!codeRunnerContent) return;
    
    // 获取所有代码单元格
    const codeCells = notebookCells.filter(cell => cell.type === 'code');
    
    if (codeCells.length === 0) {
      codeRunnerContent.innerHTML = `
        <div class="runner-placeholder">
          <p>❌ 没有找到可运行的代码</p>
          <p>请在编辑视图中添加代码块</p>
        </div>
      `;
      return;
    }
    
    // 清空运行器内容
    codeRunnerContent.innerHTML = '';
    
    // 依次运行每个代码块
    for (const [index, cell] of codeCells.entries()) {
      const blockDiv = document.createElement('div');
      blockDiv.className = 'runner-code-block';
      
      const headerDiv = document.createElement('div');
      headerDiv.className = 'runner-code-header';
      headerDiv.innerHTML = `
        <span class="runner-code-label">代码块 ${index + 1}</span>
        <span class="runner-code-label">${cell.language || 'python'}</span>
      `;
      
      const bodyDiv = document.createElement('div');
      bodyDiv.className = 'runner-code-body';
      bodyDiv.innerHTML = `<pre>${cell.content}</pre>`;
      
      blockDiv.appendChild(headerDiv);
      blockDiv.appendChild(bodyDiv);
      
      // 运行代码并显示输出
      let output = '';
      let isError = false;
      try {
        const { result } = await runNotebookCode(cell.content, cell.language || 'python');
        if (result.success) {
          output = result.output && result.output.length ? result.output : '执行完成';
        } else {
          isError = true;
          const pieces = [];
          if (result.output) pieces.push(result.output);
          if (result.message) pieces.push(result.message);
          if (result.traceback) pieces.push(result.traceback);
          output = pieces.filter(Boolean).join('\n').trim() || '执行失败';
        }
      } catch (error) {
        console.warn('批量执行 Notebook 失败，使用本地模拟', error);
        output = executeCode(cell);
        isError = output.startsWith('错误:');
      }
      
      if (output) {
        const outputDiv = document.createElement('div');
        outputDiv.className = `runner-output ${isError ? 'error' : 'success'}`;
        outputDiv.textContent = output;
        blockDiv.appendChild(outputDiv);
      }
      
      codeRunnerContent.appendChild(blockDiv);
    }
  }

  function executeCode(cell) {
    // 复用现有的runCell逻辑
    const code = cell.content.trim();
    let output = '';
    
    try {
      if (cell.language === 'python') {
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
          output = '函数已定义';
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
          output = '变量已赋值';
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
          output = '定义已完成';
        } else if (code.includes('=') && !code.includes('print')) {
          output = '执行完成';
        } else {
          output = '执行完成';
        }
      } else if (cell.language === 'javascript') {
        output = eval(code);
      } else {
        output = '执行完成';
      }
    } catch (e) {
      throw e;
    }
    
    return output;
  }

  // 轻量路由（前进后退）
  window.addEventListener('popstate', (e) => {
    if (e.state?.view === 'detail') {
      switchView('detail');
    } else if (e.state?.view === 'create') {
      switchView('create');
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
  function switchToChat(initialQuery = null, forcedAgent = null) {
    const qaWelcome = document.getElementById('qaWelcome');
    const qaChat = document.getElementById('qaChat');
    
    if (qaWelcome) qaWelcome.style.display = 'none';
    if (qaChat) qaChat.style.display = 'grid';
    
    // 获取选择的 Agent 类型
    const agentTypeSelect = document.getElementById('agentTypeSelect');
    if (forcedAgent && agentTypeSelect) {
      agentTypeSelect.value = forcedAgent;
    }
    const selectedAgent = forcedAgent || (agentTypeSelect ? agentTypeSelect.value : 'paper');
    
    // 切换到对应的标签页
    const qaTabs = document.querySelectorAll('.qa__tab');
    qaTabs.forEach(tab => {
      tab.classList.remove('is-active');
      if (tab.dataset.tab === selectedAgent) {
        tab.classList.add('is-active');
      }
    });
    
    // 显示对应的欢迎消息
    updateWelcomeMessage(selectedAgent);
    
    // 如果有初始查询，发送它
    if (initialQuery) {
      qaInput.value = initialQuery;
      sendQaMessage();
    }
  }
  
  // 更新欢迎消息函数
  function updateWelcomeMessage(agentType) {
    const messages = {
      'paper': '已切换到文献模式，我能帮你检索相关文献。',
      'research': '已切换到科研模式，我能为你提供研究建议和方法指导。',
      'code': '已切换到代码模式，我是基于 Aider AI 的代码助手，可以帮你编写、修改和优化代码。你可以：\n\n• 描述你想实现的功能，我会生成代码\n• 提供现有代码，我会帮你改进或修复bug\n• 询问代码相关的问题\n• 让我帮你重构或优化代码'
    };
    
    qaMessages.innerHTML = `<div class="msg msg--ai">
      <div class="msg__avatar">AI</div>
      <div class="msg__bubble">
        <div class="msg__content" style="white-space: pre-line;">${messages[agentType] || messages.paper}</div>
      </div>
    </div>`;
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
    
    // 获取当前激活的标签
    const activeTab = document.querySelector('.qa__tab.is-active');
    const currentMode = activeTab ? activeTab.dataset.tab : 'paper';
    
    qaMessages.insertAdjacentHTML('beforeend', `<div class="msg msg--user">
      <div class="msg__avatar">你</div>
      <div class="msg__bubble">
        <div class="msg__content">${text}</div>
      </div>
    </div>`);
    
    qaMessages.scrollTop = qaMessages.scrollHeight;
    qaInput.value = '';
    
    // 保存用户消息到会话历史
    saveMessageToHistory('user', text, currentMode);
    
    // 根据不同模式处理消息
    if (currentMode === 'code') {
      handleCodeMessage(text);
    } else if (currentMode === 'research') {
      handleResearchMessage(text);
    } else {
      handlePaperMessage(text);
    }
  }
  
  // 处理代码模式消息
  async function handleCodeMessage(text) {
    // 显示思考中状态
    const thinkingMsg = document.createElement('div');
    thinkingMsg.className = 'msg msg--ai msg--thinking';
    thinkingMsg.innerHTML = `
      <div class="msg__avatar">AI</div>
      <div class="msg__bubble">
        <div class="msg__content">
          <div class="thinking-indicator">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
          正在分析你的需求并生成代码...
        </div>
      </div>
    `;
    qaMessages.appendChild(thinkingMsg);
    qaMessages.scrollTop = qaMessages.scrollHeight;
    
    try {
      // 调用后端 Aider AI API
      const API_BASE_URL = getApiBaseUrl();
      const response = await fetch(`${API_BASE_URL}/api/code/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: text,
          language: getSelectedLanguage(),
          context: {
            files: [],
            conversation_history: []
          }
        })
      });
      
      const result = await response.json();
      
      console.log('API 返回结果:', result);
      console.log('result.success:', result.success);
      console.log('result.files:', result.files);
      
      // 移除思考中消息
      thinkingMsg.remove();
      
      if (result.success) {
        // 显示AI响应
        const responseText = result.response || result.message;
        
        // 如果有生成的文件，更新文件列表
        let filesToDisplay = [];
        if (result.files && result.files.length > 0) {
          console.log('API 返回了文件，数量:', result.files.length);
          filesToDisplay = result.files;
          updateGeneratedFiles(result.files);
          
          // 启用文件按钮
          if (qaFilesBtn) {
            qaFilesBtn.disabled = false;
            hasGeneratedFiles = true;
            console.log('文件按钮已启用');
          }
        } else {
          console.info('API 已成功返回文本，但没有附带文件，直接展示文本响应。');
          filesToDisplay = [];
        }
        
        // 使用打字机效果显示消息和代码
        try {
          await displayMessageWithTyping('ai', responseText, getCurrentAgentMode(), filesToDisplay);
        } catch (typingError) {
          console.error('打字机效果显示失败:', typingError);
          // 降级：直接显示消息
    qaMessages.insertAdjacentHTML('beforeend', `<div class="msg msg--ai">
      <div class="msg__avatar">AI</div>
      <div class="msg__bubble">
              <div class="msg__content">${responseText}</div>
      </div>
    </div>`);
        }
        
      } else {
        // 显示错误消息
        console.error('API 返回错误:', result.message);
        const errorMsg = `抱歉，代码生成失败: ${result.message}`;
        await displayMessageWithTyping('ai', errorMsg, getCurrentAgentMode());
      }
      
    } catch (error) {
      // 移除思考中消息
      thinkingMsg.remove();
      
      // 如果API不可用，生成模拟代码文件
      console.warn('Aider API 不可用，生成模拟代码文件:', error);
      
      // 生成实际的代码内容
      const mockFiles = generateMockCodeFiles(text, getSelectedLanguage());
      
      // 更新文件列表
      updateGeneratedFiles(mockFiles);
      
      const codeResponse = generateCodeResponse(text) + '\n\n注意: 当前使用模拟响应。要使用真实的 DeepSeek，请启动后端服务器。';
      
      // 使用打字机效果显示
      try {
        await displayMessageWithTyping('ai', codeResponse, getCurrentAgentMode(), mockFiles);
      } catch (typingError) {
        console.error('打字机效果显示失败:', typingError);
        // 降级：直接显示
        qaMessages.insertAdjacentHTML('beforeend', `<div class="msg msg--ai">
          <div class="msg__avatar">AI</div>
          <div class="msg__bubble">
            <div class="msg__content">${codeResponse}</div>
          </div>
        </div>`);
      }
      
      // 启用文件按钮
      if (qaFilesBtn) {
        qaFilesBtn.disabled = false;
        hasGeneratedFiles = true;
      }
    }
    
      qaMessages.scrollTop = qaMessages.scrollHeight;
  }
  
  // 获取选中的编程语言
  function getSelectedLanguage() {
    const selectedLang = document.querySelector('.language-option input:checked');
    return selectedLang ? selectedLang.value : 'python';
  }
  
  // 更新生成的文件列表（累积模式，不覆盖）
  function updateGeneratedFiles(files) {
    console.log('更新文件列表，收到文件数:', files.length);
    
    // 不再清空，改为累积添加
    // generatedFiles.length = 0;  // 注释掉，改为累积模式
    
    // 添加新文件（检查重复）
    files.forEach((file, index) => {
      // 检查是否已存在相同的文件（根据名称和内容）
      const exists = generatedFiles.find(f => 
        f.name === file.name && f.content === file.content
      );
      
      if (!exists) {
        const newFile = {
          id: Date.now() + index + Math.random() * 1000,  // 确保唯一ID
          name: file.name,
          type: file.type || 'Text',
          size: file.size || '0 KB',
          time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
          content: file.content,
          timestamp: Date.now()
        };
        generatedFiles.push(newFile);
        console.log('添加文件:', newFile.name, '大小:', newFile.size, '时间:', newFile.time);
      } else {
        console.log('文件已存在，跳过:', file.name);
      }
    });
    
    console.log('文件列表更新完成，总文件数:', generatedFiles.length);
    
    // 保存到 localStorage
    saveFilesToStorage();
  }
  
  // 保存文件列表到 localStorage
  function saveFilesToStorage() {
    const currentProjectId = getCurrentProjectId();
    if (currentProjectId) {
      try {
        const key = `agent_files_${currentProjectId}`;
        localStorage.setItem(key, JSON.stringify(generatedFiles));
        console.log('文件列表已保存到 localStorage');
      } catch (e) {
        console.error('保存文件列表失败:', e);
      }
    }
  }
  
  // 从 localStorage 加载文件列表
  function loadFilesFromStorage() {
    const currentProjectId = getCurrentProjectId();
    if (currentProjectId) {
      try {
        const key = `agent_files_${currentProjectId}`;
        const saved = localStorage.getItem(key);
        if (saved) {
          const files = JSON.parse(saved);
          generatedFiles.length = 0;
          generatedFiles.push(...files);
          console.log('从 localStorage 加载了', files.length, '个文件');
          
          // 如果有文件，启用文件按钮
          if (files.length > 0 && qaFilesBtn) {
            qaFilesBtn.disabled = false;
        hasGeneratedFiles = true;
      }
        }
      } catch (e) {
        console.error('加载文件列表失败:', e);
      }
    }
  }
  
  // 获取当前项目ID
  function getCurrentProjectId() {
    const hash = window.location.hash;
    const match = hash.match(/#project\/([^\/]+)/);
    return match ? match[1] : null;
  }
  
  // 获取当前 Agent 模式
  function getCurrentAgentMode() {
    const activeTab = document.querySelector('.qa__tab.is-active');
    return activeTab ? activeTab.dataset.tab : 'paper';
  }
  
  // HTML 转义函数
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  // 保存消息到会话历史
  function saveMessageToHistory(role, content, agentMode, files = []) {
    const projectId = getCurrentProjectId();
    if (!projectId) return;
    
    try {
      // 获取所有会话历史
      const key = `agent_conversations_${projectId}`;
      const saved = localStorage.getItem(key);
      const conversations = saved ? JSON.parse(saved) : { paper: [], research: [], code: [] };
      
      // 确保当前模式的数组存在
      if (!conversations[agentMode]) {
        conversations[agentMode] = [];
      }
      
      // 添加新消息
      conversations[agentMode].push({
        role: role,
        content: content,
        files: files,
        timestamp: Date.now(),
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      });
      
      // 保存回 localStorage
      localStorage.setItem(key, JSON.stringify(conversations));
      console.log(`会话已保存: ${role} 消息，模式: ${agentMode}`);
    } catch (e) {
      console.error('保存会话失败:', e);
    }
  }
  
  // 加载会话历史
  function loadConversationHistory(projectId) {
    if (!projectId) return;
    
    try {
      const key = `agent_conversations_${projectId}`;
      const saved = localStorage.getItem(key);
      
      if (saved) {
        const conversations = JSON.parse(saved);
        const currentMode = getCurrentAgentMode();
        const messages = conversations[currentMode] || [];
        
        console.log(`加载会话历史: ${messages.length} 条消息，模式: ${currentMode}`);
        
        // 清空当前消息区
        if (qaMessages) {
          qaMessages.innerHTML = '';
        }
        
        // 重新渲染所有历史消息
        messages.forEach(msg => {
          if (msg.role === 'user') {
            qaMessages.insertAdjacentHTML('beforeend', `<div class="msg msg--user">
              <div class="msg__avatar">你</div>
              <div class="msg__bubble">
                <div class="msg__content">${escapeHtml(msg.content)}</div>
              </div>
            </div>`);
          } else {
            let messageHTML = `<div class="msg msg--ai">
              <div class="msg__avatar">AI</div>
              <div class="msg__bubble">
                <div class="msg__content" style="white-space: pre-line;">${escapeHtml(msg.content)}</div>`;
            
            // 如果有文件，展示代码
            if (msg.files && msg.files.length > 0) {
              messageHTML += '<div class="msg-files-preview">';
              msg.files.forEach(file => {
                messageHTML += `
                  <div class="file-preview-card">
                    <div class="file-preview-header">
                      <span class="file-icon">📄</span>
                      <span class="file-name">${escapeHtml(file.name)}</span>
                      <span class="file-size">${file.size || '0 KB'}</span>
                    </div>
                    <pre class="file-preview-code"><code>${escapeHtml(file.content)}</code></pre>
                  </div>
                `;
              });
              messageHTML += '</div>';
            }
            
            messageHTML += `
              </div>
            </div>`;
            
            qaMessages.insertAdjacentHTML('beforeend', messageHTML);
          }
        });
        
        // 滚动到底部
        if (qaMessages) {
    qaMessages.scrollTop = qaMessages.scrollHeight;
        }
      }
    } catch (e) {
      console.error('加载会话历史失败:', e);
    }
  }
  
  // 检查是否有会话历史
  function checkHasConversationHistory(projectId) {
    if (!projectId) return false;
    
    try {
      const key = `agent_conversations_${projectId}`;
      const saved = localStorage.getItem(key);
      
      if (saved) {
        const conversations = JSON.parse(saved);
        // 检查所有模式是否有消息
        return Object.values(conversations).some(msgs => msgs && msgs.length > 0);
      }
    } catch (e) {
      console.error('检查会话历史失败:', e);
    }
    
    return false;
  }
  
  // 处理科研模式消息（调用 DeepSeek API）
  async function handleResearchMessage(text) {
    // 显示思考中状态
    const thinkingMsg = createThinkingMessage('正在分析研究问题...');
    qaMessages.appendChild(thinkingMsg);
    qaMessages.scrollTop = qaMessages.scrollHeight;
    
    try {
      const API_BASE_URL = getApiBaseUrl();
      const response = await fetch(`${API_BASE_URL}/api/code/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `作为科研助手，请为以下研究问题提供建议：${text}`,
          language: 'research',
          context: { mode: 'research' }
        })
      });
      
      const result = await response.json();
      thinkingMsg.remove();
      
      const responseText = result.response || result.message || `关于"${text}"的研究建议：\n\n1. 首先需要进行文献综述\n2. 确定研究方法和实验设计\n3. 收集和分析数据\n4. 撰写研究报告`;
      
      // 使用打字机效果显示
      try {
        await displayMessageWithTyping('ai', responseText, 'research');
      } catch (e) {
        console.error('打字机效果失败:', e);
        qaMessages.insertAdjacentHTML('beforeend', `<div class="msg msg--ai">
          <div class="msg__avatar">AI</div>
          <div class="msg__bubble">
            <div class="msg__content">${responseText}</div>
          </div>
        </div>`);
      }
      
    } catch (error) {
      thinkingMsg.remove();
      const responseText = `关于"${text}"的研究建议：\n\n1. 首先需要进行文献综述，了解当前研究现状\n2. 确定研究方法和实验设计\n3. 收集和分析数据\n4. 撰写研究报告\n\n需要我详细展开某个部分吗？`;
      try {
        await displayMessageWithTyping('ai', responseText, 'research');
      } catch (e) {
        console.error('打字机效果失败:', e);
        qaMessages.insertAdjacentHTML('beforeend', `<div class="msg msg--ai">
          <div class="msg__avatar">AI</div>
          <div class="msg__bubble">
            <div class="msg__content">${responseText}</div>
          </div>
        </div>`);
      }
    }
  }
  
  // 处理文献模式消息（调用 DeepSeek API）
  async function handlePaperMessage(text) {
    // 显示思考中状态
    const thinkingMsg = createThinkingMessage('正在检索相关文献...');
    qaMessages.appendChild(thinkingMsg);
    qaMessages.scrollTop = qaMessages.scrollHeight;
    
    try {
      const API_BASE_URL = getApiBaseUrl();
      const response = await fetch(`${API_BASE_URL}/api/code/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `作为文献助手，请为以下主题推荐相关文献：${text}`,
          language: 'paper',
          context: { mode: 'paper' }
        })
      });
      
      const result = await response.json();
      thinkingMsg.remove();
      
      const responseText = result.response || result.message || `我已为你检索到关于"${text}"的相关文献。以下是一些重要的研究成果：\n\n📄 相关文献将在这里显示\n\n需要我帮你分析某篇文献吗？`;
      
      // 使用打字机效果显示
      try {
        await displayMessageWithTyping('ai', responseText, 'paper');
      } catch (e) {
        console.error('打字机效果失败:', e);
        qaMessages.insertAdjacentHTML('beforeend', `<div class="msg msg--ai">
          <div class="msg__avatar">AI</div>
          <div class="msg__bubble">
            <div class="msg__content">${responseText}</div>
          </div>
        </div>`);
      }
      
    } catch (error) {
      thinkingMsg.remove();
      const responseText = `我已为你检索到关于"${text}"的相关文献。以下是一些重要的研究成果：\n\n📄 相关文献将在这里显示\n\n需要我帮你分析某篇文献吗？`;
      try {
        await displayMessageWithTyping('ai', responseText, 'paper');
      } catch (e) {
        console.error('打字机效果失败:', e);
        qaMessages.insertAdjacentHTML('beforeend', `<div class="msg msg--ai">
          <div class="msg__avatar">AI</div>
          <div class="msg__bubble">
            <div class="msg__content">${responseText}</div>
          </div>
        </div>`);
      }
    }
  }
  
  // 创建思考中消息
  function createThinkingMessage(text = '正在思考...') {
    const thinkingMsg = document.createElement('div');
    thinkingMsg.className = 'msg msg--ai msg--thinking';
    thinkingMsg.innerHTML = `
      <div class="msg__avatar">AI</div>
      <div class="msg__bubble">
        <div class="msg__content">
          <div class="thinking-indicator">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
          ${text}
        </div>
      </div>
    `;
    return thinkingMsg;
  }
  
  // 打字机效果显示消息
  async function displayMessageWithTyping(role, content, agentMode, files = []) {
    console.log('开始打字机效果显示');
    console.log('内容长度:', content.length);
    console.log('文件数:', files.length);
    
    try {
      // 创建消息容器
      const msgDiv = document.createElement('div');
      msgDiv.className = role === 'user' ? 'msg msg--user' : 'msg msg--ai';
      msgDiv.innerHTML = `
        <div class="msg__avatar">${role === 'user' ? '你' : 'AI'}</div>
        <div class="msg__bubble">
          <div class="msg__content" style="white-space: pre-line;"></div>
        </div>
      `;
      
      qaMessages.appendChild(msgDiv);
      const contentEl = msgDiv.querySelector('.msg__content');
      
      // 打字机效果
      let currentIndex = 0;
      const typingSpeed = 20; // 每个字符的延迟（毫秒）
      
      return new Promise((resolve, reject) => {
        function typeNextChar() {
          try {
            if (currentIndex < content.length) {
              contentEl.textContent += content[currentIndex];
              currentIndex++;
              qaMessages.scrollTop = qaMessages.scrollHeight;
              setTimeout(typeNextChar, typingSpeed);
            } else {
              // 打字完成后，如果有文件，添加文件预览
              console.log('打字完成，准备添加文件预览');
              if (files && files.length > 0) {
                let filesHTML = '<div class="msg-files-preview">';
                files.forEach(file => {
                  filesHTML += `
                    <div class="file-preview-card">
                      <div class="file-preview-header">
                        <span class="file-icon">📄</span>
                        <span class="file-name">${escapeHtml(file.name)}</span>
                        <span class="file-size">${file.size || '0 KB'}</span>
                      </div>
                      <pre class="file-preview-code"><code>${escapeHtml(file.content)}</code></pre>
                    </div>
                  `;
                });
                filesHTML += '</div>';
                msgDiv.querySelector('.msg__bubble').insertAdjacentHTML('beforeend', filesHTML);
                console.log('文件预览已添加');
              }
              
              // 保存到会话历史
              saveMessageToHistory(role, content, agentMode, files);
              console.log('打字机效果完成');
              resolve();
            }
          } catch (err) {
            console.error('打字机循环出错:', err);
            reject(err);
          }
        }
        
        typeNextChar();
      });
    } catch (error) {
      console.error('displayMessageWithTyping 函数出错:', error);
      throw error;
    }
  }
  
  // 生成模拟代码文件
  function generateMockCodeFiles(userQuery, language) {
    console.log('开始生成模拟代码文件');
    console.log('用户查询:', userQuery);
    console.log('语言:', language);
    
    const query = userQuery.toLowerCase();
    const files = [];
    
    // 根据用户查询生成相应的代码
    if (query.includes('快速排序') || query.includes('quicksort') || query.includes('排序')) {
      console.log('匹配到: 快速排序');
      files.push({
        id: Date.now(),
        name: `quicksort.${getFileExtension(language)}`,
        type: getLanguageName(language),
        size: '1.2 KB',
        time: '刚刚',
        content: generateQuickSortCode(language)
      });
    } else if (query.includes('二分查找') || query.includes('binary search')) {
      files.push({
        id: Date.now(),
        name: `binary_search.${getFileExtension(language)}`,
        type: getLanguageName(language),
        size: '0.8 KB',
        time: '刚刚',
        content: generateBinarySearchCode(language)
      });
    } else if (query.includes('web') || query.includes('网页') || query.includes('网站')) {
      files.push(
        {
          id: Date.now(),
          name: 'index.html',
          type: 'HTML',
          size: '2.1 KB',
          time: '刚刚',
          content: generateHTMLCode()
        },
        {
          id: Date.now() + 1,
          name: 'styles.css',
          type: 'CSS',
          size: '1.5 KB',
          time: '刚刚',
          content: generateCSSCode()
        },
        {
          id: Date.now() + 2,
          name: 'script.js',
          type: 'JavaScript',
          size: '1.8 KB',
          time: '刚刚',
          content: generateJSCode()
        }
      );
    } else {
      // 默认生成一个示例文件
      console.log('使用默认代码生成');
      files.push({
        id: Date.now(),
        name: `example.${getFileExtension(language)}`,
        type: getLanguageName(language),
        size: '1.0 KB',
        time: '刚刚',
        content: generateDefaultCode(language, userQuery)
      });
    }
    
    console.log('生成的文件数:', files.length);
    files.forEach(f => console.log('文件:', f.name, '类型:', f.type));
    
    return files;
  }
  
  // 生成快速排序代码
  function generateQuickSortCode(language) {
    if (language === 'python') {
      return `def quicksort(arr):
    """
    快速排序算法实现
    时间复杂度: O(n log n) 平均情况
    空间复杂度: O(log n)
    """
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quicksort(left) + middle + quicksort(right)


# 测试代码
if __name__ == "__main__":
    test_arr = [64, 34, 25, 12, 22, 11, 90]
    print("原始数组:", test_arr)
    sorted_arr = quicksort(test_arr)
    print("排序后:", sorted_arr)`;
    } else if (language === 'javascript') {
      return `function quicksort(arr) {
    /**
     * 快速排序算法实现
     * 时间复杂度: O(n log n) 平均情况
     * 空间复杂度: O(log n)
     */
    if (arr.length <= 1) {
        return arr;
    }
    
    const pivot = arr[Math.floor(arr.length / 2)];
    const left = arr.filter(x => x < pivot);
    const middle = arr.filter(x => x === pivot);
    const right = arr.filter(x => x > pivot);
    
    return [...quicksort(left), ...middle, ...quicksort(right)];
}

// 测试代码
const testArr = [64, 34, 25, 12, 22, 11, 90];
console.log("原始数组:", testArr);
const sortedArr = quicksort(testArr);
console.log("排序后:", sortedArr);`;
    }
    return `// ${language} 快速排序实现\n// 请根据具体语言实现`;
  }
  
  // 生成二分查找代码
  function generateBinarySearchCode(language) {
    if (language === 'python') {
      return `def binary_search(arr, target):
    """
    二分查找算法
    前提: 数组必须已排序
    时间复杂度: O(log n)
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1  # 未找到


# 测试代码
if __name__ == "__main__":
    sorted_arr = [11, 12, 22, 25, 34, 64, 90]
    target = 25
    result = binary_search(sorted_arr, target)
    print(f"查找 {target}: 索引 {result}")`;
    }
    return `// ${language} 二分查找实现`;
  }
  
  // 生成HTML代码
  function generateHTMLCode() {
    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的网页</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>欢迎来到我的网站</h1>
        <nav>
            <a href="#home">首页</a>
            <a href="#about">关于</a>
            <a href="#contact">联系</a>
        </nav>
    </header>
    
    <main>
        <section id="home">
            <h2>主页内容</h2>
            <p>这是一个示例网页</p>
        </section>
    </main>
    
    <footer>
        <p>&copy; 2024 我的网站</p>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>`;
  }
  
  // 生成CSS代码
  function generateCSSCode() {
    return `* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    color: #333;
}

header {
    background: #35424a;
    color: #ffffff;
    padding: 20px;
    text-align: center;
}

nav a {
    color: #ffffff;
    text-decoration: none;
    padding: 0 15px;
}

main {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
}

footer {
    background: #35424a;
    color: #ffffff;
    text-align: center;
    padding: 10px;
    position: fixed;
    bottom: 0;
    width: 100%;
}`;
  }
  
  // 生成JavaScript代码
  function generateJSCode() {
    return `// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面已加载');
    
    // 导航链接点击事件
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                targetSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});`;
  }
  
  // 生成默认代码
  function generateDefaultCode(language, query) {
    if (language === 'python') {
      return `"""
${query}
生成的 Python 代码示例
"""

def main():
    print("Hello, World!")
    print("这是根据您的需求生成的代码框架")
    # TODO: 在这里添加具体实现

if __name__ == "__main__":
    main()`;
    } else if (language === 'javascript') {
      return `/**
 * ${query}
 * 生成的 JavaScript 代码示例
 */

function main() {
    console.log("Hello, World!");
    console.log("这是根据您的需求生成的代码框架");
    // TODO: 在这里添加具体实现
}

main();`;
    }
    return `// ${query}\n// 代码框架`;
  }
  
  // 获取文件扩展名
  function getFileExtension(language) {
    const extensions = {
      'python': 'py',
      'javascript': 'js',
      'java': 'java',
      'c': 'c'
    };
    return extensions[language] || 'txt';
  }
  
  // 获取语言名称
  function getLanguageName(language) {
    const names = {
      'python': 'Python',
      'javascript': 'JavaScript',
      'java': 'Java',
      'c': 'C'
    };
    return names[language] || 'Text';
  }
  
  // 生成代码响应（模拟Aider AI）
  function generateCodeResponse(userQuery) {
    // 这里将来会调用真实的Aider AI API
    // 现在先返回模拟响应
    const responses = {
      'python': '我已经为你生成了Python代码。代码包含了完整的实现，包括必要的导入、函数定义和使用示例。',
      'web': '我已经为你生成了Web应用代码，包括HTML、CSS和JavaScript文件。',
      'api': '我已经为你生成了API接口代码，包括路由定义、控制器和数据模型。',
      'default': '我已经为你生成了完整的代码框架，包括主要功能实现和配置文件。你可以点击右上角的"文件"按钮查看和下载这些文件。'
    };
    
    const query = userQuery.toLowerCase();
    if (query.includes('python') || query.includes('py')) {
      return responses.python;
    } else if (query.includes('web') || query.includes('网页') || query.includes('前端')) {
      return responses.web;
    } else if (query.includes('api') || query.includes('接口')) {
      return responses.api;
    }
    
    return responses.default;
  }

  qaTabs.forEach(tab => tab.addEventListener('click', () => {
    qaTabs.forEach(t => t.classList.remove('is-active'));
    tab.classList.add('is-active');
    
    // 切换标签时，加载该模式的会话历史
    const projectId = getCurrentProjectId();
    if (projectId) {
      loadConversationHistory(projectId);
    } else {
      // 如果没有项目ID，显示默认欢迎消息
      let modeText = '文献';
      let welcomeMessage = '已切换到文献模式，我能帮你检索相关文献。';
      
      if (tab.dataset.tab === 'research') {
        modeText = '科研';
        welcomeMessage = '已切换到科研模式，我能为你提供研究建议和方法指导。';
      } else if (tab.dataset.tab === 'code') {
        modeText = '代码';
        welcomeMessage = '已切换到代码模式，我是基于 Aider AI 的代码助手，可以帮你编写、修改和优化代码。你可以：\n\n• 描述你想实现的功能，我会生成代码\n• 提供现有代码，我会帮你改进或修复bug\n• 询问代码相关的问题\n• 让我帮你重构或优化代码';
      }
      
    qaMessages.innerHTML = `<div class="msg msg--ai">
      <div class="msg__avatar">AI</div>
      <div class="msg__bubble">
          <div class="msg__content" style="white-space: pre-line;">${welcomeMessage}</div>
      </div>
    </div>`;
    }
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
      console.log('文件按钮被点击，当前文件数:', generatedFiles.length);
      console.log('文件列表:', generatedFiles);
      
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
    
    console.log('渲染文件列表，文件数:', generatedFiles.length);
    
    if (generatedFiles.length === 0) {
      filesList.innerHTML = '<div class="files-empty">暂无生成的文件</div>';
      return;
    }
    
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
  const generateVideoBtn = document.getElementById('generateVideoBtn');
  const highlightTextBtn = document.getElementById('highlightText');
  const highlightColors = document.getElementById('highlightColors');
  const underlineTextBtn = document.getElementById('underlineText');
  const strikeTextBtn = document.getElementById('strikeText');
  const searchTextBtn = document.getElementById('searchText');
  const searchOptions = document.getElementById('searchOptions');
  const clearFormatBtn = document.getElementById('clearFormatBtn');
  
  let selectedText = '';
  let selectedRange = null;
  let currentSection = ''; // 当前所在的分区

  // 允许使用划词工具栏的分区
  const allowedSections = ['background', 'model', 'model-intro', 'baseline', 'idea', 'personalize', 'comments'];

  // 检查当前是否在允许的分区
  function isInAllowedSection() {
    return allowedSections.includes(currentSection);
  }

  // 监听文本选择
  document.addEventListener('mouseup', (e) => {
    const selection = window.getSelection();
    const text = selection.toString().trim();
    
    if (text && text.length > 0) {
      // 检查是否在允许的分区
      if (!isInAllowedSection()) {
        textToolbar.style.display = 'none';
        return;
      }
      
      selectedText = text;
      selectedRange = selection.getRangeAt(0);
      if (searchOptions) searchOptions.style.display = 'none';
      
      // 显示工具栏
      const rect = selectedRange.getBoundingClientRect();
      textToolbar.style.display = 'flex';
      textToolbar.style.left = `${rect.left + window.scrollX + (rect.width / 2) - 100}px`;
      textToolbar.style.top = `${rect.top + window.scrollY - 45}px`;
    } else {
      textToolbar.style.display = 'none';
      highlightColors.style.display = 'none';
      if (searchOptions) searchOptions.style.display = 'none';
    }
  });

  // 点击其他地方关闭工具栏
  document.addEventListener('mousedown', (e) => {
    if (textToolbar && !textToolbar.contains(e.target) && !e.target.closest('.markdown-rendered')) {
      textToolbar.style.display = 'none';
      highlightColors.style.display = 'none';
      if (searchOptions) searchOptions.style.display = 'none';
    }
  });

  // 生成讲解视频
  if (generateVideoBtn) {
    generateVideoBtn.addEventListener('click', () => {
      if (selectedText) {
        // 触发生成讲解视频事件（接口待接入）
        window.dispatchEvent(new CustomEvent('notebook:generateVideo', { 
          detail: { text: selectedText } 
        }));
        
        // 显示占位消息
        if (qaMessages) {
          qaMessages.insertAdjacentHTML('beforeend', `<div class="msg msg--ai">
            <div class="msg__avatar">AI</div>
            <div class="msg__bubble">
              <div class="msg__content">生成讲解视频接口待接入。\n选中内容: ${selectedText}</div>
            </div>
          </div>`);
          qaMessages.scrollTop = qaMessages.scrollHeight;
        } else {
          alert(`生成讲解视频接口待接入。\n选中内容: ${selectedText}`);
        }
        
        textToolbar.style.display = 'none';
        window.getSelection().removeAllRanges();
        selectedText = '';
        selectedRange = null;
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

  if (searchTextBtn && searchOptions) {
    searchTextBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (!selectedText) return;
      searchOptions.style.display = searchOptions.style.display === 'none' ? 'flex' : 'none';
    });
  }

  if (searchOptions) {
    const optionButtons = searchOptions.querySelectorAll('button[data-type]');
    optionButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        handleSearchAction(btn.dataset.type);
      });
    });
  }

  if (clearFormatBtn) {
    clearFormatBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      clearFormatting();
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
      selectedRange = null;
      selectedText = '';
    } catch (e) {
      console.error('应用高亮失败:', e);
      // 备用方法：使用document.execCommand
      try {
        document.execCommand('backColor', false, color);
        saveAnnotations();
        selectedRange = null;
        selectedText = '';
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
      selectedRange = null;
      selectedText = '';
    } catch (e) {
      console.error('应用下划线失败:', e);
      try {
        document.execCommand('underline', false, null);
        saveAnnotations();
        selectedRange = null;
        selectedText = '';
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
      selectedRange = null;
      selectedText = '';
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

  function unwrapNode(node) {
    const parent = node.parentNode;
    if (!parent) return;
    while (node.firstChild) {
      parent.insertBefore(node.firstChild, node);
    }
    parent.removeChild(node);
  }

  function removeFormattingByClass(className) {
    if (!selectedRange) return false;
    let ancestor = selectedRange.commonAncestorContainer;
    if (ancestor && ancestor.nodeType !== 1) {
      ancestor = ancestor.parentElement;
    }
    if (!ancestor || !ancestor.querySelectorAll) return false;
    const targets = ancestor.querySelectorAll(`.${className}`);
    let changed = false;
    targets.forEach(node => {
      try {
        if (selectedRange.intersectsNode(node)) {
          unwrapNode(node);
          changed = true;
        }
      } catch (e) {
        // 忽略跨文档的节点
      }
    });
    if (changed) {
      saveAnnotations();
    }
    return changed;
  }

  function clearFormatting() {
    // 清除整个内容区所有标注（不限于选中区域）
    const content = document.getElementById('detailContent');
    if (!content) return;
    
    const allHighlights = content.querySelectorAll('.text-highlight');
    const allUnderlines = content.querySelectorAll('.text-underline');
    const allStrikes = content.querySelectorAll('.text-strike');
    
    allHighlights.forEach(node => unwrapNode(node));
    allUnderlines.forEach(node => unwrapNode(node));
    allStrikes.forEach(node => unwrapNode(node));
    
    saveAnnotations();
    
    window.getSelection().removeAllRanges();
    selectedRange = null;
    selectedText = '';
    if (textToolbar) textToolbar.style.display = 'none';
    if (highlightColors) highlightColors.style.display = 'none';
    if (searchOptions) searchOptions.style.display = 'none';
    
    alert('已清除所有标注');
  }

  function handleSearchAction(type) {
    if (searchOptions) {
      searchOptions.style.display = 'none';
    }
    if (type === 'cancel') return;
    if (!selectedText) return;
    const query = selectedText;
    selectedText = '';
    if (type === 'code') {
      switchToChat(query, 'code');
      window.getSelection().removeAllRanges();
      textToolbar.style.display = 'none';
      selectedRange = null;
      return;
    }
    if (type === 'paper' || type === 'research') {
      showSearchPlaceholder(type, query);
      window.dispatchEvent(new CustomEvent('notebook:search', { detail: { type, query } }));
      window.getSelection().removeAllRanges();
      textToolbar.style.display = 'none';
      selectedRange = null;
    }
  }

  function showSearchPlaceholder(mode, query) {
    const labels = {
      paper: '文献搜索',
      research: '科研搜索'
    };
    const message = `${labels[mode] || '搜索'}接口待接入。\n关键词: ${query}`;
    if (qaMessages) {
      qaMessages.insertAdjacentHTML('beforeend', `<div class="msg msg--ai">
        <div class="msg__avatar">AI</div>
        <div class="msg__bubble">
          <div class="msg__content" style="white-space: pre-line;">${message}</div>
        </div>
      </div>`);
      qaMessages.scrollTop = qaMessages.scrollHeight;
    } else {
      alert(message);
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

  // ============================================
  // 出题功能模块 - Problem Creation Module
  // ============================================
  // 作者: zhaoziwei
  // 说明: 独立的出题功能模块，通过数据接口与其他模块交互
  
  (function ProblemCreationModule() {
    'use strict';  // 严格模式，避免变量污染
    
    // ========== 模块配置 ==========
    const MODULE_NAME = 'ProblemCreation';
    const STORAGE_KEY_PENDING = 'ai_platform_pending_problems';
    const STORAGE_KEY_PROJECTS = 'ai_platform_projects';
    
    // ========== DOM 元素（模块私有） ==========
    const createView = qs('#create-view');
    const createProblemForm = qs('#createProblemForm');
    const backFromCreateBtn = qs('#backFromCreateBtn');
    const closeCreateViewBtn = qs('#closeCreateViewBtn');
    const cancelCreateBtn = qs('#cancelCreateBtn');
    const themeToggle3 = qs('#themeToggle3');
    
    // ========== 数据接口函数（对外暴露） ==========
    
    /**
     * 获取待审核题目列表
     * @returns {Array} 待审核题目数组
     */
    function getPendingProblems() {
      try {
        const data = localStorage.getItem(STORAGE_KEY_PENDING);
        return data ? JSON.parse(data) : [];
      } catch (e) {
        console.error(`[${MODULE_NAME}] 读取待审核题目失败:`, e);
        return [];
      }
    }
    
    /**
     * 保存待审核题目列表
     * @param {Array} problems - 题目数组
     */
    function savePendingProblems(problems) {
      try {
        localStorage.setItem(STORAGE_KEY_PENDING, JSON.stringify(problems));
        // 触发自定义事件，通知其他模块数据已更新
        window.dispatchEvent(new CustomEvent('pendingProblemsUpdated', {
          detail: { problems }
        }));
        console.log(`[${MODULE_NAME}] 待审核题目已保存，数量:`, problems.length);
      } catch (e) {
        console.error(`[${MODULE_NAME}] 保存待审核题目失败:`, e);
      }
    }
    
    /**
     * 获取已发布项目列表
     * @returns {Array} 项目数组
     */
    function getPublishedProjects() {
      try {
        const data = localStorage.getItem(STORAGE_KEY_PROJECTS);
        return data ? JSON.parse(data) : [];
      } catch (e) {
        console.error(`[${MODULE_NAME}] 读取项目列表失败:`, e);
        return [];
      }
    }
    
    /**
     * 添加新项目到已发布列表（由审核模块调用）
     * @param {Object} project - 项目对象
     */
    function addPublishedProject(project) {
      try {
        const projects = getPublishedProjects();
        projects.push(project);
        localStorage.setItem(STORAGE_KEY_PROJECTS, JSON.stringify(projects));
        // 触发自定义事件，通知其他模块数据已更新
        window.dispatchEvent(new CustomEvent('projectsUpdated', {
          detail: { projects }
        }));
        console.log(`[${MODULE_NAME}] 项目已添加:`, project.title);
      } catch (e) {
        console.error(`[${MODULE_NAME}] 添加项目失败:`, e);
      }
    }
    
    // ========== 模块内部函数 ==========
    
    /**
     * 获取当前用户角色（从全局状态）
     */
    function getCurrentUserRole() {
      return window.currentUserRole || currentUserRole || 'user';
    }
    
    /**
     * 获取当前用户名（从全局状态或 profileSubs）
     */
    function getCurrentUsername() {
      const profileSub = qs('.profile__sub');
      if (profileSub) {
        const text = profileSub.textContent;
        const match = text.match(/·\s*(.+?)$/);
        if (match && match[1] && match[1] !== '访客' && match[1] !== '研究者') {
          return match[1].trim();
        }
      }
      return getCurrentUserRole();
    }
    
    /**
     * 收集表单数据
     */
    function collectFormData() {
      if (!createProblemForm) return null;
      
      const baseData = {
        title: qs('#problemTitle', createProblemForm)?.value.trim() || '',
        category: qs('#problemCategory', createProblemForm)?.value || '',
        subKey: qs('#problemSubKey', createProblemForm)?.value.trim() || '',
        desc: qs('#problemDesc', createProblemForm)?.value.trim() || ''
      };
      
      // 收集详情内容（如果配置系统可用）
      let detailContent = null;
      if (window.ProjectStructureConfig) {
        detailContent = {};
        const formSections = window.ProjectStructureConfig.getFormSections();
        
        formSections.forEach(section => {
          const sectionData = collectSectionData(section);
          if (sectionData !== null) {
            detailContent[section.key] = sectionData;
          }
        });
        
        // 如果没有任何详情内容，设置为null
        if (Object.keys(detailContent).length === 0) {
          detailContent = null;
        }
      }
      
      return {
        ...baseData,
        detailContent: detailContent
      };
    }
    
    /**
     * 收集单个章节的数据
     */
    function collectSectionData(sectionConfig) {
      switch (sectionConfig.type) {
        case 'notebook':
          return collectNotebookSectionData(sectionConfig.key);
        case 'quiz':
          return collectQuizSectionData(sectionConfig.key);
        case 'comments':
          return null; // 留言区不需要在表单中收集
        default:
          return null;
      }
    }
    
    /**
     * 收集Notebook章节数据
     */
    function collectNotebookSectionData(sectionKey) {
      const editor = qs(`.notebook-editor[data-section-key="${sectionKey}"]`, createProblemForm);
      if (!editor) return null;
      
      const cells = [];
      const cellEditors = editor.querySelectorAll('.notebook-cell-editor');
      
      cellEditors.forEach(cellEl => {
        const type = cellEl.dataset.cellType; // 'markdown' or 'code'
        const content = cellEl.querySelector('.cell-content-input')?.value.trim() || '';
        const language = cellEl.dataset.language || 'python';
        
        if (content) {
          cells.push({ type, content, language });
        }
      });
      
      return cells.length > 0 ? cells : null;
    }
    
    /**
     * 收集个性化检验数据
     */
    function collectQuizSectionData(sectionKey) {
      const editor = qs(`.quiz-editor[data-section-key="${sectionKey}"]`, createProblemForm);
      if (!editor) return null;
      
      const questions = [];
      const questionEditors = editor.querySelectorAll('.quiz-question-editor');
      
      questionEditors.forEach(qEl => {
        const question = qEl.querySelector('.question-input')?.value.trim();
        const options = [];
        const optionInputs = qEl.querySelectorAll('.option-input');
        
        optionInputs.forEach(opt => {
          const value = opt.value.trim();
          if (value) options.push(value);
        });
        
        const correctRadio = qEl.querySelector('input[type="radio"]:checked');
        const correct = correctRadio ? parseInt(correctRadio.value) : 0;
        
        if (question && options.length === 4) {
          questions.push({ question, options, correct });
        }
      });
      
      return questions.length > 0 ? questions : null;
    }
    
    /**
     * 验证表单数据
     */
    function validateFormData(data) {
      if (!data) {
        showErrorMessage('表单数据无效');
        return false;
      }
      
      if (!data.title || !data.category || !data.subKey || !data.desc) {
        showErrorMessage('请填写所有必填字段！');
        return false;
      }
      
      // 验证子分类键格式
      const subKeyPattern = /^[a-z0-9-]+$/;
      if (!subKeyPattern.test(data.subKey)) {
        showErrorMessage('子分类键格式不正确！请使用英文小写字母、数字和连字符。');
        return false;
      }
      
      return true;
    }
    
    /**
     * 创建题目对象
     */
    function createProblemObject(formData) {
      const userRole = getCurrentUserRole();
      const username = getCurrentUsername();
      
      return {
        // 基础信息
        id: 'p' + Date.now(),
        category: formData.category,
        subKey: formData.subKey,
        title: formData.title,
        desc: formData.desc,
        
        // 状态信息
        status: 'pending',
        likes: 0,
        createdAt: new Date().toISOString(),
        createdBy: userRole,
        createdByUsername: username,
        
        // 详情内容（从表单收集）
        detailContent: formData.detailContent || null
      };
    }
    
    /**
     * 处理表单提交
     */
    function handleFormSubmit(e) {
      e.preventDefault();
      console.log(`[${MODULE_NAME}] 表单提交`);
      
      // 收集表单数据
      const formData = collectFormData();
      
      // 验证数据
      if (!validateFormData(formData)) {
        return;
      }
      
      // 创建题目对象
      const problem = createProblemObject(formData);
      console.log(`[${MODULE_NAME}] 创建题目对象:`, problem);
      
      // 保存到待审核列表
      const pendingList = getPendingProblems();
      pendingList.push(problem);
      savePendingProblems(pendingList);
      
      // 显示成功提示
      showSuccessMessage('题目已提交，等待管理员审核！');
      
      // 重置表单
      createProblemForm.reset();
      
      // 返回首页
      navigateToHome();
    }
    
    /**
     * 导航到首页
     */
    function navigateToHome() {
      console.log(`[${MODULE_NAME}] 导航到首页`);
      
      // 更新 URL
      if (window.history && window.history.pushState) {
        window.history.pushState({ view: 'home' }, '', '#');
      }
      
      // 调用全局的视图切换函数
      if (typeof window.switchView === 'function') {
        window.switchView('home');
      }
      
      // 调用首页视图函数（如果存在）
      if (typeof window.showHomeView === 'function') {
        window.showHomeView();
      }
    }
    
    /**
     * 显示成功消息
     */
    function showSuccessMessage(message) {
      alert(message);  // 使用简单的 alert，后续可替换为更优雅的提示
    }
    
    /**
     * 显示错误消息
     */
    function showErrorMessage(message) {
      alert(message);  // 使用简单的 alert，后续可替换为更优雅的提示
    }
    
    /**
     * 动态生成详情内容表单
     * 基于 ProjectStructureConfig 配置自动生成
     */
    function generateDetailContentForm() {
      const container = qs('#dynamicSectionsContainer', createProblemForm);
      const formSection = qs('#detailContentFormSection', createProblemForm);
      
      if (!container) {
        console.warn(`[${MODULE_NAME}] 动态表单容器未找到`);
        return;
      }
      
      // 检查配置系统是否可用
      if (!window.ProjectStructureConfig) {
        console.warn(`[${MODULE_NAME}] ProjectStructureConfig 未加载，跳过动态表单生成`);
        return;
      }
      
      container.innerHTML = '';
      
      // 从配置获取需要在表单中显示的章节
      const formSections = window.ProjectStructureConfig.getFormSections();
      
      formSections.forEach(section => {
        const sectionEditor = createSectionEditor(section);
        if (sectionEditor) {
          container.appendChild(sectionEditor);
        }
      });
      
      // 显示表单区域
      if (formSection && formSections.length > 0) {
        formSection.style.display = 'block';
      }
      
      console.log(`[${MODULE_NAME}] 已生成 ${formSections.length} 个章节编辑器`);
    }
    
    /**
     * 创建单个章节编辑器
     */
    function createSectionEditor(sectionConfig) {
      const sectionDiv = document.createElement('div');
      sectionDiv.className = 'form-section-item';
      sectionDiv.dataset.sectionKey = sectionConfig.key;
      
      const header = document.createElement('div');
      header.className = 'form-section-item-header';
      header.innerHTML = `
        <h3 class="form-section-item-title">
          ${sectionConfig.name}
          ${sectionConfig.required ? '<span class="required">*</span>' : ''}
        </h3>
        <p class="form-section-item-desc">${sectionConfig.description || ''}</p>
      `;
      sectionDiv.appendChild(header);
      
      const content = document.createElement('div');
      content.className = 'form-section-item-content';
      
      // 根据章节类型创建对应的编辑器
      switch (sectionConfig.type) {
        case 'notebook':
          content.appendChild(createNotebookEditor(sectionConfig));
          break;
        case 'quiz':
          content.appendChild(createQuizEditor(sectionConfig));
          break;
        case 'comments':
          // 留言区不需要编辑器
          content.innerHTML = '<p class="form-hint">留言区将在项目发布后自动创建，无需在此设置初始内容。</p>';
          break;
        default:
          console.warn(`[${MODULE_NAME}] 未支持的章节类型: ${sectionConfig.type}`);
          return null;
      }
      
      sectionDiv.appendChild(content);
      return sectionDiv;
    }
    
    /**
     * 创建Notebook编辑器
     */
    function createNotebookEditor(sectionConfig) {
      const editor = document.createElement('div');
      editor.className = 'notebook-editor';
      editor.dataset.sectionKey = sectionConfig.key;
      
      const cellsContainer = document.createElement('div');
      cellsContainer.className = 'notebook-cells-container';
      editor.appendChild(cellsContainer);
      
      // 添加默认单元格（如果配置中有）
      const defaultCells = sectionConfig.notebookConfig?.defaultCells || [];
      defaultCells.forEach((cellData, index) => {
        const cellEditor = createNotebookCellEditor(cellData, index);
        cellsContainer.appendChild(cellEditor);
      });
      
      // 如果没有默认单元格，添加一个空的Markdown单元格
      if (defaultCells.length === 0) {
        const cellEditor = createNotebookCellEditor({ type: 'markdown', content: '' }, 0);
        cellsContainer.appendChild(cellEditor);
      }
      
      // 添加单元格按钮
      const actions = document.createElement('div');
      actions.className = 'notebook-editor-actions';
      actions.innerHTML = `
        <button type="button" class="btn btn--ghost btn--small add-markdown-cell">+ Markdown</button>
        <button type="button" class="btn btn--ghost btn--small add-code-cell">+ Code</button>
      `;
      
      actions.querySelector('.add-markdown-cell').addEventListener('click', () => {
        const cellEditor = createNotebookCellEditor({ type: 'markdown', content: '' }, cellsContainer.children.length);
        cellsContainer.appendChild(cellEditor);
        cellEditor.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      });
      
      actions.querySelector('.add-code-cell').addEventListener('click', () => {
        const cellEditor = createNotebookCellEditor({
          type: 'code',
          content: '',
          language: sectionConfig.notebookConfig?.defaultLanguage || 'python'
        }, cellsContainer.children.length);
        cellsContainer.appendChild(cellEditor);
        cellEditor.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      });
      
      editor.appendChild(actions);
      return editor;
    }
    
    /**
     * 创建Notebook单元格编辑器
     */
    function createNotebookCellEditor(cellData, index) {
      const cellDiv = document.createElement('div');
      cellDiv.className = 'notebook-cell-editor';
      cellDiv.dataset.cellIndex = index;
      cellDiv.dataset.cellType = cellData.type || 'markdown';
      cellDiv.dataset.language = cellData.language || 'python';
      
      const header = document.createElement('div');
      header.className = 'notebook-cell-editor-header';
      
      const typeSelect = document.createElement('select');
      typeSelect.className = 'cell-type-select';
      typeSelect.innerHTML = `
        <option value="markdown" ${cellData.type === 'markdown' ? 'selected' : ''}>Markdown</option>
        <option value="code" ${cellData.type === 'code' ? 'selected' : ''}>Code</option>
      `;
      
      const languageSelect = document.createElement('select');
      languageSelect.className = 'cell-language-select';
      languageSelect.style.display = cellData.type === 'code' ? 'inline-block' : 'none';
      languageSelect.innerHTML = `
        <option value="python" ${cellData.language === 'python' ? 'selected' : ''}>Python</option>
        <option value="javascript" ${cellData.language === 'javascript' ? 'selected' : ''}>JavaScript</option>
      `;
      
      const deleteBtn = document.createElement('button');
      deleteBtn.type = 'button';
      deleteBtn.className = 'btn btn--ghost btn--tiny delete-cell-btn';
      deleteBtn.textContent = '删除';
      deleteBtn.addEventListener('click', () => {
        cellDiv.remove();
        // 更新索引
        const container = cellDiv.parentElement;
        const cells = container.querySelectorAll('.notebook-cell-editor');
        cells.forEach((cell, idx) => {
          cell.dataset.cellIndex = idx;
        });
      });
      
      header.appendChild(typeSelect);
      header.appendChild(languageSelect);
      header.appendChild(deleteBtn);
      
      const contentTextarea = document.createElement('textarea');
      contentTextarea.className = 'cell-content-input';
      contentTextarea.value = cellData.content || '';
      contentTextarea.placeholder = cellData.type === 'markdown' 
        ? '输入 Markdown 内容...' 
        : '输入代码...';
      contentTextarea.rows = 5;
      
      typeSelect.addEventListener('change', (e) => {
        cellDiv.dataset.cellType = e.target.value;
        languageSelect.style.display = e.target.value === 'code' ? 'inline-block' : 'none';
      });
      
      languageSelect.addEventListener('change', (e) => {
        cellDiv.dataset.language = e.target.value;
      });
      
      cellDiv.appendChild(header);
      cellDiv.appendChild(contentTextarea);
      
      return cellDiv;
    }
    
    /**
     * 创建个性化检验编辑器
     */
    function createQuizEditor(sectionConfig) {
      const editor = document.createElement('div');
      editor.className = 'quiz-editor';
      editor.dataset.sectionKey = sectionConfig.key;
      
      const questionsContainer = document.createElement('div');
      questionsContainer.className = 'quiz-questions-container';
      editor.appendChild(questionsContainer);
      
      // 添加默认题目（如果配置中有）
      const defaultQuestions = sectionConfig.quizConfig?.defaultQuizData || [];
      if (defaultQuestions.length > 0) {
        defaultQuestions.forEach((questionData, index) => {
          const questionEditor = createQuizQuestionEditor(questionData, index);
          questionsContainer.appendChild(questionEditor);
        });
      } else {
        // 如果没有默认题目，添加一个空题目
        const questionEditor = createQuizQuestionEditor({
          question: '',
          options: ['', '', '', ''],
          correct: 0
        }, 0);
        questionsContainer.appendChild(questionEditor);
      }
      
      // 添加题目按钮
      const addBtn = document.createElement('button');
      addBtn.type = 'button';
      addBtn.className = 'btn btn--ghost btn--small add-question-btn';
      addBtn.textContent = '+ 添加题目';
      addBtn.addEventListener('click', () => {
        const maxQuestions = sectionConfig.quizConfig?.maxQuestions || 10;
        if (questionsContainer.children.length >= maxQuestions) {
          alert(`最多只能添加 ${maxQuestions} 道题目`);
          return;
        }
        const questionEditor = createQuizQuestionEditor({
          question: '',
          options: ['', '', '', ''],
          correct: 0
        }, questionsContainer.children.length);
        questionsContainer.appendChild(questionEditor);
        questionEditor.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      });
      
      editor.appendChild(addBtn);
      return editor;
    }
    
    /**
     * 创建题目编辑器
     */
    function createQuizQuestionEditor(questionData, index) {
      const questionDiv = document.createElement('div');
      questionDiv.className = 'quiz-question-editor';
      questionDiv.dataset.questionIndex = index;
      
      const header = document.createElement('div');
      header.className = 'quiz-question-editor-header';
      header.innerHTML = `<span class="question-number">第 ${index + 1} 题</span>`;
      
      const deleteBtn = document.createElement('button');
      deleteBtn.type = 'button';
      deleteBtn.className = 'btn btn--ghost btn--tiny delete-question-btn';
      deleteBtn.textContent = '删除';
      deleteBtn.addEventListener('click', () => {
        questionDiv.remove();
        // 更新题目编号
        const container = questionDiv.parentElement;
        const questions = container.querySelectorAll('.quiz-question-editor');
        questions.forEach((q, idx) => {
          const numSpan = q.querySelector('.question-number');
          if (numSpan) numSpan.textContent = `第 ${idx + 1} 题`;
          q.dataset.questionIndex = idx;
        });
      });
      header.appendChild(deleteBtn);
      
      const questionInput = document.createElement('textarea');
      questionInput.className = 'question-input';
      questionInput.value = questionData.question || '';
      questionInput.placeholder = '输入问题...';
      questionInput.rows = 2;
      
      const optionsContainer = document.createElement('div');
      optionsContainer.className = 'quiz-options-container';
      
      questionData.options.forEach((option, optIndex) => {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'quiz-option-editor';
        
        const optionLabel = document.createElement('label');
        optionLabel.className = 'option-label';
        optionLabel.textContent = String.fromCharCode(65 + optIndex);
        
        const optionInput = document.createElement('input');
        optionInput.type = 'text';
        optionInput.className = 'option-input';
        optionInput.value = option || '';
        optionInput.placeholder = `选项 ${String.fromCharCode(65 + optIndex)}`;
        
        const correctRadio = document.createElement('input');
        correctRadio.type = 'radio';
        correctRadio.name = `correct_${questionDiv.dataset.questionIndex}`;
        correctRadio.value = optIndex;
        correctRadio.checked = optIndex === questionData.correct;
        
        optionDiv.appendChild(correctRadio);
        optionDiv.appendChild(optionLabel);
        optionDiv.appendChild(optionInput);
        optionsContainer.appendChild(optionDiv);
      });
      
      questionDiv.appendChild(header);
      questionDiv.appendChild(questionInput);
      questionDiv.appendChild(optionsContainer);
      
      return questionDiv;
    }
    
    /**
     * 初始化表单
     */
    function initForm() {
      if (!createProblemForm) {
        console.warn(`[${MODULE_NAME}] 表单元素未找到`);
        return;
      }
      
      // 动态生成详情内容表单
      generateDetailContentForm();
      
      // 绑定提交事件
      createProblemForm.addEventListener('submit', handleFormSubmit);
      console.log(`[${MODULE_NAME}] 表单事件已绑定`);
    }
    
    /**
     * 初始化导航按钮
     */
    function initNavigationButtons() {
      // 返回主页按钮（侧边栏）
      if (backFromCreateBtn) {
        backFromCreateBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          console.log(`[${MODULE_NAME}] 返回按钮被点击`);
          navigateToHome();
        });
      }
      
      // 关闭按钮（头部）
      if (closeCreateViewBtn) {
        closeCreateViewBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          console.log(`[${MODULE_NAME}] 关闭按钮被点击`);
          navigateToHome();
        });
      }
      
      // 取消按钮（表单）
      if (cancelCreateBtn) {
        cancelCreateBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          console.log(`[${MODULE_NAME}] 取消按钮被点击`);
          
          // 询问是否确认取消
          if (createProblemForm && createProblemForm.checkValidity && createProblemForm.checkValidity()) {
            const formData = collectFormData();
            if (formData && (formData.title || formData.desc)) {
              if (confirm('表单有未保存的内容，确定要取消吗？')) {
                createProblemForm.reset();
                navigateToHome();
              }
              return;
            }
          }
          
          createProblemForm.reset();
          navigateToHome();
        });
      }
      
      console.log(`[${MODULE_NAME}] 导航按钮事件已绑定`);
    }
    
    /**
     * 初始化主题切换（出题页面）
     */
    function initThemeToggle() {
      if (themeToggle3) {
        themeToggle3.addEventListener('click', () => {
          document.body.classList.toggle('theme-dark');
          document.body.classList.toggle('theme-light');
        });
      }
    }
    
    /**
     * 模块初始化
     */
    function init() {
      if (!createView) {
        console.warn(`[${MODULE_NAME}] 出题视图未找到，模块未初始化`);
        return;
      }
      
      initForm();
      initNavigationButtons();
      initThemeToggle();
      
      console.log(`[${MODULE_NAME}] 模块初始化完成 ✓`);
    }
    
    // ========== 模块导出 ==========
    // 将需要对外暴露的函数挂载到全局对象
    
    window.ProblemCreation = {
      getPendingProblems,
      savePendingProblems,
      getPublishedProjects,
      addPublishedProject,
      init
    };
    
    // 自动初始化
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
    
  })();
  // ========== 出题功能模块结束 ==========

  // ============================================
  // 审核功能模块 - Admin Review Module
  // ============================================
  // 作者: zhaoziwei
  // 说明: 管理员审核功能模块，与出题模块协同工作
  
  (function AdminReviewModule() {
    'use strict';  // 严格模式
    
    // ========== 模块配置 ==========
    const MODULE_NAME = 'AdminReview';
    
    // ========== DOM 元素（模块私有） ==========
    const adminReviewBtn = qs('#adminReviewBtn');
    const adminReviewModal = qs('#adminReviewModal');
    const closeReviewModal = qs('#closeReviewModal');
    const reviewList = qs('#reviewList');
    
    // ========== 辅助函数 ==========
    
    /**
     * 格式化日期时间
     */
    function formatDateTime(isoString) {
      const date = new Date(isoString);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
    
    /**
     * 获取分类中文名
     */
    function getCategoryName(categoryKey) {
      const categoryNames = {
        'image': '图像',
        'audio': '语音',
        'llm': 'LLM',
        'mllm': 'MLLM',
        'agent': 'Agent'
      };
      return categoryNames[categoryKey] || categoryKey;
    }
    
    /**
     * 获取角色中文名
     */
    function getRoleName(roleKey) {
      const roleNames = {
        'enterprise': '企业',
        'teacher': '高校教师',
        'user': '普通使用者'
      };
      return roleNames[roleKey] || roleKey;
    }
    
    // ========== 核心功能函数 ==========
    
    /**
     * 渲染审核列表
     */
    function renderReviewList() {
      if (!reviewList) {
        console.warn(`[${MODULE_NAME}] reviewList 元素未找到`);
        return;
      }
      
      // 获取待审核列表
      const pendingProblems = window.ProblemCreation 
        ? window.ProblemCreation.getPendingProblems() 
        : [];
      
      console.log(`[${MODULE_NAME}] 待审核题目数量:`, pendingProblems.length);
      
      // 如果没有待审核题目
      if (pendingProblems.length === 0) {
        reviewList.innerHTML = '<div class="review-empty">暂无待审核题目</div>';
        return;
      }
      
      // 渲染审核条目
      reviewList.innerHTML = '';
      
      pendingProblems.forEach((problem, index) => {
        const item = document.createElement('div');
        item.className = 'review-item';
        item.setAttribute('data-index', index);
        
        item.innerHTML = `
          <div class="review-item__header">
            <div>
              <h3 class="review-item__title">${problem.title}</h3>
              <div class="review-item__meta">
                <span>提交者：${getRoleName(problem.createdBy)} · ${problem.createdByUsername}</span>
                <span>提交时间：${formatDateTime(problem.createdAt)}</span>
              </div>
            </div>
            <span class="review-item__status review-item__status--pending">待审核</span>
          </div>
          
          <div class="review-item__content">
            <div class="review-item__field">
              <div class="review-item__field-label">分类</div>
              <div class="review-item__field-value">${getCategoryName(problem.category)} / ${problem.subKey}</div>
            </div>
            
            <div class="review-item__field">
              <div class="review-item__field-label">项目描述</div>
              <div class="review-item__field-value">${problem.desc}</div>
            </div>
            
            ${problem.background ? `
              <div class="review-item__field">
                <div class="review-item__field-label">背景介绍</div>
                <div class="review-item__field-value pre-wrap">${problem.background}</div>
              </div>
            ` : ''}
          </div>
          
          <div class="review-item__actions">
            <button class="btn btn--ghost reject-btn" data-index="${index}">拒绝</button>
            <button class="btn btn--primary approve-btn" data-index="${index}">批准发布</button>
          </div>
        `;
        
        reviewList.appendChild(item);
      });
      
      // 绑定批准/拒绝按钮事件
      bindReviewActions();
    }
    
    /**
     * 绑定审核操作按钮事件
     */
    function bindReviewActions() {
      // 批准按钮
      const approveBtns = reviewList.querySelectorAll('.approve-btn');
      approveBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const index = parseInt(btn.getAttribute('data-index'));
          approveProblem(index);
        });
      });
      
      // 拒绝按钮
      const rejectBtns = reviewList.querySelectorAll('.reject-btn');
      rejectBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const index = parseInt(btn.getAttribute('data-index'));
          rejectProblem(index);
        });
      });
    }
    
    /**
     * 批准题目
     */
    function approveProblem(index) {
      console.log(`[${MODULE_NAME}] 批准题目，索引:`, index);
      
      if (!window.ProblemCreation) {
        console.error(`[${MODULE_NAME}] ProblemCreation 模块未找到`);
        return;
      }
      
      // 确认操作
      if (!confirm('确定要批准这个题目并发布到项目列表吗？')) {
        return;
      }
      
      // 获取待审核列表
      const pendingList = window.ProblemCreation.getPendingProblems();
      
      if (index < 0 || index >= pendingList.length) {
        alert('题目索引无效');
        return;
      }
      
      // 获取题目
      const problem = pendingList[index];
      
      // 修改状态为已批准
      problem.status = 'approved';
      problem.reviewedAt = new Date().toISOString();
      problem.reviewedBy = getCurrentUsername();
      
      // 从待审核列表移除
      pendingList.splice(index, 1);
      window.ProblemCreation.savePendingProblems(pendingList);
      
      // 添加到已发布项目列表
      window.ProblemCreation.addPublishedProject(problem);
      
      // 提示成功
      alert('题目已批准并发布！');
      
      // 重新渲染审核列表
      renderReviewList();
      
      console.log(`[${MODULE_NAME}] 题目已批准:`, problem.title);
    }
    
    /**
     * 拒绝题目
     */
    function rejectProblem(index) {
      console.log(`[${MODULE_NAME}] 拒绝题目，索引:`, index);
      
      if (!window.ProblemCreation) {
        console.error(`[${MODULE_NAME}] ProblemCreation 模块未找到`);
        return;
      }
      
      // 询问拒绝原因
      const reason = prompt('请输入拒绝原因（将通知提交者）：');
      
      if (reason === null) {
        // 用户取消
        return;
      }
      
      if (!reason.trim()) {
        alert('请输入拒绝原因');
        return;
      }
      
      // 获取待审核列表
      const pendingList = window.ProblemCreation.getPendingProblems();
      
      if (index < 0 || index >= pendingList.length) {
        alert('题目索引无效');
        return;
      }
      
      // 获取题目
      const problem = pendingList[index];
      
      // 记录拒绝信息（可选：保存到历史记录）
      problem.status = 'rejected';
      problem.reviewedAt = new Date().toISOString();
      problem.reviewedBy = getCurrentUsername();
      problem.rejectReason = reason.trim();
      
      // 从待审核列表移除
      pendingList.splice(index, 1);
      window.ProblemCreation.savePendingProblems(pendingList);
      
      // 提示成功
      alert(`题目已拒绝。拒绝原因：${reason.trim()}`);
      
      // 重新渲染审核列表
      renderReviewList();
      
      console.log(`[${MODULE_NAME}] 题目已拒绝:`, problem.title);
    }
    
    /**
     * 获取当前用户名
     */
    function getCurrentUsername() {
      const profileSub = qs('.profile__sub');
      if (profileSub) {
        const text = profileSub.textContent;
        const match = text.match(/·\s*(.+?)$/);
        if (match && match[1] && match[1] !== '访客' && match[1] !== '研究者') {
          return match[1].trim();
        }
      }
      return 'admin';
    }
    
    /**
     * 初始化审核按钮
     */
    function initReviewButton() {
      if (!adminReviewBtn) {
        console.warn(`[${MODULE_NAME}] adminReviewBtn 元素未找到`);
        return;
      }
      
      adminReviewBtn.addEventListener('click', () => {
        console.log(`[${MODULE_NAME}] 审核按钮被点击`);
        renderReviewList();
        if (adminReviewModal) {
          adminReviewModal.classList.add('active');
        }
      });
      
      console.log(`[${MODULE_NAME}] 审核按钮事件已绑定`);
    }
    
    /**
     * 初始化关闭按钮
     */
    function initCloseButton() {
      if (closeReviewModal) {
        closeReviewModal.addEventListener('click', () => {
          if (adminReviewModal) {
            adminReviewModal.classList.remove('active');
          }
        });
      }
      
      // 点击遮罩层关闭
      if (adminReviewModal) {
        adminReviewModal.addEventListener('click', (e) => {
          if (e.target === adminReviewModal || e.target.classList.contains('modal__overlay')) {
            adminReviewModal.classList.remove('active');
          }
        });
        
        // 阻止模态框内容区域的点击事件冒泡
        const modalContent = adminReviewModal.querySelector('.modal__content');
        if (modalContent) {
          modalContent.addEventListener('click', (e) => {
            e.stopPropagation();
          });
        }
      }
    }
    
    /**
     * 模块初始化
     */
    function init() {
      if (!adminReviewModal) {
        console.warn(`[${MODULE_NAME}] 审核模态框未找到，模块未初始化`);
        return;
      }
      
      initReviewButton();
      initCloseButton();
      
      console.log(`[${MODULE_NAME}] 模块初始化完成 ✓`);
    }
    
    // ========== 模块导出 ==========
    
    window.AdminReview = {
      renderReviewList,
      approveProblem,
      rejectProblem,
      init
    };
    
    // 自动初始化
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
    
  })();
  // ========== 审核功能模块结束 ==========

  // 初始化
  showHomeView();
  // 恢复主题
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.body.classList.remove('theme-light');
    document.body.classList.add('theme-dark');
  }
})();


