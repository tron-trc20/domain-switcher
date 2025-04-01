const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const path = require('path');
const mongoose = require('mongoose');
const Domain = require('./models/domain');

const app = express();
const PORT = process.env.PORT || 3000;
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'admin123';

// 直接硬编码MongoDB连接字符串（生产环境中通常不推荐，但为了解决当前问题）
const MONGODB_URI = 'mongodb+srv://panzer:panzer@cluster0.yacqmwk.mongodb.net/domain_manager?retryWrites=true&w=majority&appName=Cluster0';

// 连接MongoDB
mongoose.connect(MONGODB_URI, { useNewUrlParser: true, useUnifiedTopology: true })
  .then(() => console.log('MongoDB连接成功'))
  .catch(err => console.error('MongoDB连接失败:', err));

// 会话中间件
const session = require('express-session');
app.use(session({
  secret: process.env.SESSION_SECRET || 'your-secret-key',
  resave: false,
  saveUninitialized: false,
  cookie: { secure: process.env.NODE_ENV === 'production' }
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
  if (password === ADMIN_PASSWORD) {
    req.session.isAuthenticated = true;
    res.json({ success: true });
  } else {
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
  if (req.session.isAuthenticated) {
    express.static(path.join(__dirname, '../admin'))(req, res, next);
  } else {
    res.redirect('/admin/login.html');
  }
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
    const { url } = req.body;
    if (!url) {
      return res.status(400).json({ error: '域名URL不能为空' });
    }

    const domain = new Domain({ url });
    await domain.save();
    
    res.status(201).json({ message: '域名添加成功', domain });
  } catch (error) {
    console.error('添加域名错误:', error);
    if (error.code === 11000) { // MongoDB重复键错误
      res.status(400).json({ error: '该域名已存在' });
    } else {
      res.status(500).json({ error: '添加域名失败' });
    }
  }
});

// API - 批量添加域名（需要登录）
app.post('/api/domains/batch', requireAuth, async (req, res) => {
  try {
    const { urls } = req.body;
    if (!urls || !Array.isArray(urls) || urls.length === 0) {
      return res.status(400).json({ error: '域名列表不能为空' });
    }

    const domains = urls.map(url => ({ url }));
    const result = await Domain.insertMany(domains, { ordered: false });
    
    res.status(201).json({ 
      message: `成功添加${result.length}个域名`,
      domains: result
    });
  } catch (error) {
    console.error('批量添加域名错误:', error);
    if (error.writeErrors) {
      // 部分插入成功的情况
      const successCount = error.insertedDocs.length;
      res.status(207).json({
        message: `部分域名添加成功（${successCount}/${urls.length}个）`,
        error: '部分域名可能已存在'
      });
    } else {
      res.status(500).json({ error: '批量添加域名失败' });
    }
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