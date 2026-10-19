'use client';

export default function GlobalError({ reset }: { error: Error; reset: () => void }) {
  return (
    <html lang="zh-CN">
      <body
        style={{ fontFamily: 'Microsoft YaHei, sans-serif', padding: '12vh 10%', color: '#222b2e' }}
      >
        <h1>网站暂时没有打开</h1>
        <p>内容服务可能正在维护，请稍后重试。</p>
        <button onClick={reset} style={{ padding: '12px 24px', cursor: 'pointer' }}>
          重新加载
        </button>
      </body>
    </html>
  );
}
