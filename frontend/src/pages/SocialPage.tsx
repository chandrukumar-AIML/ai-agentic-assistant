// frontend/src/pages/SocialPage.tsx — Feature 19: Social Media Manager
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { generateContent, generateHashtags, generateImage } from '../lib/api'

const TOPICS = ['AI in Healthcare India', 'Startup funding tips', 'Python best practices', 'Climate change solutions', 'Digital marketing trends']
const PLATFORMS = [{ label: 'LinkedIn', value: 'linkedin' }, { label: 'Twitter/X', value: 'twitter' }, { label: 'Instagram', value: 'instagram' }, { label: 'Facebook', value: 'facebook' }]
const TONES = [{ label: 'Professional', value: 'professional' }, { label: 'Casual', value: 'casual' }, { label: 'Inspirational', value: 'inspirational' }, { label: 'Educational', value: 'educational' }, { label: 'Humorous', value: 'humorous' }]

export default function SocialPage() {
  const [tab, setTab]         = useState('content')
  const [topic, setTopic]     = useState(TOPICS[0])
  const [platform, setPlatform] = useState('linkedin')
  const [tone, setTone]       = useState('professional')
  const [imgPrompt, setImgPrompt] = useState('Modern AI technology with Indian corporate professionals')
  const [hashTag, setHashTag] = useState('AI startups India')

  const contentApi = useApi()
  const hashApi    = useApi()
  const imgApi     = useApi()

  return (
    <PageShell icon="📱" title="AI Social Media Manager" subtitle="Feature 19 — LinkedIn + Twitter/X + DALL-E 3 + Buffer scheduling">
      <Tabs
        tabs={[
          { id: 'content',  label: 'Content Generator', icon: '✍️' },
          { id: 'hashtags', label: 'Hashtag Research',  icon: '#️⃣' },
          { id: 'image',    label: 'AI Image',          icon: '🎨' },
        ]}
        active={tab} onChange={setTab}
      />

      {tab === 'content' && (
        <TwoCol>
          <Card>
            <SectionHead title="Social Content Generator" sub="Platform-optimized posts with character limits" />
            <Select label="Platform" value={platform} onChange={setPlatform} options={PLATFORMS} />
            <Select label="Tone" value={tone} onChange={setTone} options={TONES} />
            <div style={{ marginBottom: 10 }}>
              {TOPICS.map(t => (
                <button key={t} onClick={() => setTopic(t)} style={{
                  display: 'block', width: '100%', textAlign: 'left', padding: '6px 10px', marginBottom: 4,
                  background: topic === t ? 'rgba(99,102,241,0.1)' : 'none', border: `1px solid ${topic === t ? '#6366f1' : '#1e2535'}`,
                  borderRadius: 6, color: topic === t ? '#a5b4fc' : '#6b7280', fontSize: 12, cursor: 'pointer',
                }}>{t}</button>
              ))}
            </div>
            <Input label="Custom Topic" value={topic} onChange={setTopic} />
            <Btn onClick={() => contentApi.call(() => generateContent(topic, platform, tone))} loading={contentApi.loading}>
              ✍️ Generate Content
            </Btn>
          </Card>

          <div>
            {contentApi.data && !contentApi.loading && (() => {
              // API returns { posts: { [platform]: { post_text, hashtags, char_count, ... } } }
              const post = contentApi.data.posts?.[platform] || contentApi.data
              const postText = post.post_text || post.content || ''
              const hashtags: string[] = post.hashtags || contentApi.data.hashtags || []
              const charCount: number = post.char_count || postText.length
              return (
                <Card style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                    <Badge text={platform.toUpperCase()} color="blue" />
                    <Badge text={tone} color="purple" />
                    {post.model && <Badge text="Ollama" color="purple" />}
                  </div>
                  {postText && (
                    <div style={{ background: '#0f1117', borderRadius: 8, padding: 16, marginBottom: 10 }}>
                      <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                        {postText}
                      </div>
                      <div style={{ marginTop: 8, color: '#6b7280', fontSize: 11 }}>
                        {charCount} / {post.max_chars || 3000} characters
                      </div>
                    </div>
                  )}
                  {hashtags.length > 0 && (
                    <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                      {hashtags.slice(0, 8).map((h: string) => (
                        <span key={h} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 20, background: 'rgba(99,102,241,0.15)', color: '#a5b4fc' }}>
                          {h.startsWith('#') ? h : `#${h}`}
                        </span>
                      ))}
                    </div>
                  )}
                </Card>
              )
            })()}
            <ResultBox data={contentApi.data} loading={contentApi.loading} error={contentApi.error} title="Generated Content" />
          </div>
        </TwoCol>
      )}

      {tab === 'hashtags' && (
        <TwoCol>
          <Card>
            <SectionHead title="Hashtag Research" sub="Trending + niche hashtags for maximum reach" />
            <Select label="Platform" value={platform} onChange={setPlatform} options={PLATFORMS} />
            <Input label="Topic" value={hashTag} onChange={setHashTag} />
            <Btn onClick={() => hashApi.call(() => generateHashtags(hashTag, platform))} loading={hashApi.loading}>
              #️⃣ Find Hashtags
            </Btn>
          </Card>

          <div>
            {hashApi.data?.hashtags && (
              <Card style={{ marginBottom: 12 }}>
                <SectionHead title="Recommended Hashtags" />
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {hashApi.data.hashtags.map((h: string, i: number) => (
                    <span key={i} style={{
                      fontSize: 12, padding: '4px 10px', borderRadius: 20, cursor: 'pointer',
                      background: i < 5 ? 'rgba(99,102,241,0.2)' : 'rgba(34,197,94,0.1)',
                      color: i < 5 ? '#a5b4fc' : '#86efac',
                      border: `1px solid ${i < 5 ? 'rgba(99,102,241,0.3)' : 'rgba(34,197,94,0.2)'}`,
                    }}>
                      {h.startsWith('#') ? h : `#${h}`}
                    </span>
                  ))}
                </div>
              </Card>
            )}
            <ResultBox data={hashApi.data} loading={hashApi.loading} error={hashApi.error} title="Hashtag Data" />
          </div>
        </TwoCol>
      )}

      {tab === 'image' && (
        <TwoCol>
          <Card>
            <SectionHead title="AI Image Generation" sub="DALL-E 3 — 1024×1024 social media images" />
            <Input label="Image Prompt" value={imgPrompt} onChange={setImgPrompt} rows={3} />
            <div style={{ marginBottom: 12 }}>
              {['Modern AI technology with Indian corporate professionals','Vibrant startup ecosystem in Bengaluru','Digital transformation in Indian agriculture'].map(p => (
                <button key={p} onClick={() => setImgPrompt(p)} style={{
                  display: 'block', width: '100%', textAlign: 'left', padding: '6px 10px', marginBottom: 4,
                  background: '#0f1117', border: '1px solid #1e2535', borderRadius: 6, color: '#6b7280', fontSize: 11, cursor: 'pointer',
                }}>{p}</button>
              ))}
            </div>
            <Btn onClick={() => imgApi.call(() => generateImage(imgPrompt))} loading={imgApi.loading}>
              🎨 Generate Image
            </Btn>
          </Card>
          <div>
            {imgApi.data?.image_url && (
              <Card style={{ marginBottom: 12 }}>
                <img src={imgApi.data.image_url} alt="Generated" style={{ width: '100%', borderRadius: 8 }} />
                <div style={{ marginTop: 8, fontSize: 11, color: '#6b7280' }}>
                  DALL-E 3 • 1024×1024 • {imgApi.data.model || 'dall-e-3'}
                </div>
              </Card>
            )}
            <ResultBox data={imgApi.data} loading={imgApi.loading} error={imgApi.error} title="Image Response" />
          </div>
        </TwoCol>
      )}
    </PageShell>
  )
}
