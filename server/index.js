const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const path = require('path');
const mongoose = require('mongoose');

// 直接定义域名模型
const domainSchema = new mongoose.Schema({
  url: { type: String, required: true },
  enabled: { type: Boolean, default: true },
  createdAt: { type: Date, default: Date.now }
});

// 确保模型名称的一致性（首字母大写）
const Domain = mongoose.model('Domain', domainSchema);
console.log('Mongoose模型已创建:', Domain.modelName);

const app = express();
const PORT = process.env.PORT || 3000;
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'admin123';

// 直接硬编码MongoDB连接字符串（生产环境中通常不推荐，但为了解决当前问题）
const MONGODB_URI = 'mongodb+srv://panzer:Aa563214aa%2E@cluster0.yacqmwk.mongodb.net/domain_manager?retryWrites=true&w=majority&appName=Cluster0';

// 连接MongoDB
mongoose.connect(MONGODB_URI, { useNewUrlParser: true, useUnifiedTopology: true })
  .then(() => console.log('MongoDB连接成功'))
  .catch(err => console.error('MongoDB连接失败:', err));

// 会话中间件
const session = require('express-session');
app.use(session({
  secret: process.env.SESSION_SECRET || 'your-secret-key',
  resave: false,
  saveUninitialized: true,
  cookie: { 
    secure: process.env.NODE_ENV === 'production' && false,
    maxAge: 24 * 60 * 60 * 1000
  }
}));

// 中间件
app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, '../public')));

// 登录验证中间件
const requireAuth = (req, res, next) => {
  if (req.session.isAuthenticated) {
    next();
  } else {
    res.status(401).json({ error: '请先登录' });
  }
};

// 登录API
app.post('/api/login', (req, res) => {
  const { password } = req.body;
  console.log('尝试登录，提供的密码:', password);
  console.log('环境中的密码:', ADMIN_PASSWORD);
  
  // 允许使用环境变量中的密码或固定测试密码"admin123"
  if (password === ADMIN_PASSWORD || password === 'admin123') {
    req.session.isAuthenticated = true;
    console.log('登录成功，会话已设置');
    res.json({ success: true });
  } else {
    console.log('登录失败，密码不匹配');
    res.status(401).json({ error: '密码错误' });
  }
});

// 登出API
app.post('/api/logout', (req, res) => {
  req.session.destroy();
  res.json({ success: true });
});

// 管理后台（需要先登录）
app.use('/admin', (req, res, next) => {
  // 如果是登录页面，允许直接访问
  if (req.path === '/login.html' || req.path === '/') {
    express.static(path.join(__dirname, '../admin'))(req, res, next);
  } else if (req.session.isAuthenticated) {
    express.static(path.join(__dirname, '../admin'))(req, res, next);
  } else {
    res.redirect('/admin/login.html');
  }
});

// 直接提供登录页面
app.get('/admin/login', (req, res) => {
  res.sendFile(path.join(__dirname, '../admin/login.html'));
});

// 直接提供登录页面（另一种URL形式）
app.get('/admin/login.html', (req, res) => {
  res.sendFile(path.join(__dirname, '../admin/login.html'));
});

// 主页 - 重定向逻辑
app.get('/', async (req, res) => {
  try {
    console.log('收到主页请求，准备跳转...');
    const enabledDomains = await Domain.find({ enabled: true }).sort({ createdAt: 1 });
    console.log('启用的域名:', enabledDomains.length ? enabledDomains.map(d => d.url).join(', ') : '无');
    
    if (enabledDomains.length > 0) {
      const targetUrl = enabledDomains[0].url;
      console.log('将跳转到:', targetUrl);
      return res.redirect(targetUrl);
    } else {
      console.log('没有可用的跳转域名');
      return res.send('没有可用的跳转域名');
    }
  } catch (error) {
    console.error('重定向错误:', error);
    res.status(500).send('服务器错误: ' + error.message);
  }
});

// 自定义页面用于测试重定向
app.get('/test-redirect', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>重定向测试</title>
      <meta charset="UTF-8">
    </head>
    <body>
      <h1>重定向测试页面</h1>
      <p>点击下面的按钮测试重定向：</p>
      <button onclick="testRedirect()">测试重定向</button>
      <script>
        function testRedirect() {
          window.location.href = '/';
        }
      </script>
    </body>
    </html>
  `);
});

// API - 获取所有域名（需要登录）
app.get('/api/domains', requireAuth, async (req, res) => {
  try {
    const domains = await Domain.find().sort({ createdAt: 1 });
    res.json({ domains });
  } catch (error) {
    console.error('获取域名错误:', error);
    res.status(500).json({ error: '获取域名列表失败' });
  }
});

// API - 添加单个域名（需要登录）
app.post('/api/domains', requireAuth, async (req, res) => {
  try {
    let { url } = req.body;
    if (!url) {
      return res.status(400).json({ error: '域名URL不能为空' });
    }

    // 自动添加协议前缀（如果没有）
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url;
    }

    console.log('添加域名尝试:', url);
    
    // 检查域名是否已存在
    const existingDomain = await Domain.findOne({ url });
    if (existingDomain) {
      console.log('域名已存在:', url);
      return res.status(400).json({ error: '该域名已存在' });
    }

    // 创建新域名
    const domain = new Domain({ url });
    const savedDomain = await domain.save();
    console.log('域名添加成功:', savedDomain);
    
    res.status(201).json({ message: '域名添加成功', domain: savedDomain });
  } catch (error) {
    console.error('添加域名错误详情:', error);
    // 返回详细的错误信息
    res.status(500).json({ 
      error: '添加域名失败',
      details: error.message,
      code: error.code || 'unknown'
    });
  }
});

// API - 批量添加域名（需要登录）
app.post('/api/domains/batch', requireAuth, async (req, res) => {
  try {
    let { urls } = req.body;
    console.log('接收到的批量域名数据:', req.body);
    
    if (typeof req.body.urls === 'string') {
      // 尝试从文本框解析多行输入
      urls = req.body.urls.split('\n')
        .map(url => url.trim())
        .filter(url => url.length > 0);
      
      console.log('从文本解析的域名列表:', urls);
    }
    
    if (!urls || urls.length === 0) {
      return res.status(400).json({ error: '域名列表不能为空' });
    }

    // 添加协议前缀
    const processedUrls = urls.map(url => {
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        return 'https://' + url;
      }
      return url;
    });
    
    console.log('处理后的域名列表:', processedUrls);
    
    // 创建文档
    const domains = processedUrls.map(url => ({ url }));
    
    // 保存到数据库
    const savedDomains = [];
    for (const domain of domains) {
      try {
        // 逐个添加域名，忽略已存在的
        const exists = await Domain.findOne({ url: domain.url });
        if (!exists) {
          const newDomain = new Domain(domain);
          const saved = await newDomain.save();
          savedDomains.push(saved);
        }
      } catch (innerError) {
        console.error(`添加域名 ${domain.url} 失败:`, innerError);
      }
    }
    
    if (savedDomains.length > 0) {
      res.status(201).json({
        message: `成功添加${savedDomains.length}个域名`,
        domains: savedDomains
      });
    } else {
      res.status(400).json({ error: '所有域名都已存在或添加失败' });
    }
  } catch (error) {
    console.error('批量添加域名错误:', error);
    res.status(500).json({ 
      error: '批量添加域名失败',
      details: error.message
    });
  }
});

// API - 更新域名状态（需要登录）
app.put('/api/domains/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const { enabled } = req.body;
    
    if (enabled === undefined) {
      return res.status(400).json({ error: '缺少状态参数' });
    }

    // 检查ID是否有效
    if (!id || id === 'undefined') {
      return res.status(400).json({ error: '无效的域名ID' });
    }

    // 检查ID是否为有效的MongoDB ObjectId
    if (!mongoose.Types.ObjectId.isValid(id)) {
      return res.status(400).json({ error: '域名ID格式不正确' });
    }

    const domain = await Domain.findByIdAndUpdate(
      id,
      { enabled },
      { new: true }
    );
    
    if (!domain) {
      return res.status(404).json({ error: '域名不存在' });
    }
    
    res.json({ message: '域名状态更新成功', domain });
  } catch (error) {
    console.error('更新域名错误:', error);
    res.status(500).json({ error: '更新域名状态失败' });
  }
});

// API - 删除域名（需要登录）
app.delete('/api/domains/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    
    // 检查ID是否有效
    if (!id || id === 'undefined') {
      return res.status(400).json({ error: '无效的域名ID' });
    }

    // 检查ID是否为有效的MongoDB ObjectId
    if (!mongoose.Types.ObjectId.isValid(id)) {
      return res.status(400).json({ error: '域名ID格式不正确' });
    }
    
    const domain = await Domain.findByIdAndDelete(id);
    
    if (!domain) {
      return res.status(404).json({ error: '域名不存在' });
    }
    
    res.json({ message: '域名删除成功' });
  } catch (error) {
    console.error('删除域名错误:', error);
    res.status(500).json({ error: '删除域名失败' });
  }
});

// API - 公共获取第一个启用的域名（不需要登录）
app.get('/api/first-domain', async (req, res) => {
  try {
    const enabledDomains = await Domain.find({ enabled: true }).sort({ createdAt: 1 });
    
    if (enabledDomains.length > 0) {
      res.json({ url: enabledDomains[0].url });
    } else {
      res.json({ url: null, message: '没有可用的跳转域名' });
    }
  } catch (error) {
    console.error('获取域名错误:', error);
    res.status(500).json({ error: '获取域名失败' });
  }
});

// 保活路由
app.get('/ping', (req, res) => {
  res.send('pong');
});

// 启动服务器
app.listen(PORT, () => {
  console.log(`服务器运行在 http://localhost:${PORT}`);
  console.log(`管理后台地址: http://localhost:${PORT}/admin`);
  console.log(`重定向测试页: http://localhost:${PORT}/test-redirect`);
}); 