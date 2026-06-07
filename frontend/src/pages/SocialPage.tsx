// frontend/src/pages/SocialPage.tsx — Feature 19: Social Media Manager
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { generateContent, generateHashtags, generateImage, socialEnhance } from '../lib/api'

const TOPICS    = ['AI in Healthcare India', 'Startup funding tips', 'Python best practices', 'Climate change solutions', 'Digital marketing trends']
const PLATFORMS = [{ label: 'LinkedIn', value: 'linkedin' }, { label: 'Twitter/X', value: 'twitter' }, { label: 'Instagram', value: 'instagram' }, { label: 'Facebook', value: 'facebook' }]
const TONES     = [{ label: 'Professional', value: 'professional' }, { label: 'Casual', value: 'casual' }, { label: 'Inspirational', value: 'inspirational' }, { label: 'Educational', value: 'educational' }, { label: 'Humorous', value: 'humorous' }]

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

  // SEO Audit tab
  const [seoUrl, setSeoUrl]               = useState('https://yourdomain.com/product')
  const [seoKeywords, setSeoKeywords]     = useState('AI platform India, enterprise automation, B2B SaaS India')
  const [seoCompetitors, setSeoCompetitors] = useState('competitor1.com, competitor2.com')
  const [seoContent, setSeoContent]       = useState('')
  const seoApi = useApi()

  // Campaign Brief tab
  const [campProduct, setCampProduct]   = useState('AI Agentic Platform — Enterprise Edition')
  const [campAudience, setCampAudience] = useState('CTOs and VP Engineering at 200–2000 employee tech companies in India')
  const [campBudget, setCampBudget]     = useState('₹5,00,000 / month')
  const [campTimeline, setCampTimeline] = useState('3 months (Q1 2026)')
  const [campChannels, setCampChannels] = useState('LinkedIn Ads, Google Search, Email nurture, Content marketing')
  const [campGoal, setCampGoal]         = useState('Generate 50 qualified leads per month at CPL < ₹10,000')
  const campaignApi = useApi()

  return (
    <PageShell icon="📱" title="AI Social Media Manager" subtitle="Content, hashtags, AI images, SEO audits & campaign briefs">
      <Tabs
        tabs={[
          { id: 'content',  label: 'Content Generator', icon: '✍️' },
          { id: 'hashtags', label: 'Hashtag Research',  icon: '#️⃣' },
          { id: 'image',    label: 'AI Image',          icon: '🎨' },
          { id: 'seo',      label: 'SEO Audit',         icon: '🔍' },
          { id: 'campaign', label: 'Campaign Brief',     icon: '📋' },
        ]}
        active={tab} onChange={setTab}
      />

      {tab === 'content' && (
        <TwoCol>
          <Card>
            <SectionHead title="Social Content Generator" sub="Platform-optimized posts with character limits" />
            <Select label="Platform" value={platform} onChange={setPlatform} options={PLATFORMS} />
            <Select label="Tone"     value={tone}     onChange={setTone}     options={TONES} />
            <div style={{ marginBottom: 10 }}>
              {TOPICS.map(t => (
                <button key={t} onClick={() => setTopic(t)} style={{
                  display: 'block', width: '100%', textAlign: 'left', padding: '6px 10px', marginBottom: 4,
                  background: topic === t ? 'rgba(16,185,129,0.1)' : 'none', border: `1px solid ${topic === t ? '#10b981' : '#1e2535'}`,
                  borderRadius: 6, color: topic === t ? '#5eead4' : '#6b7280', fontSize: 12, cursor: 'pointer',
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
              const post = contentApi.data.posts?.[platform] || contentApi.data
              const postText = post.post_text || post.content || ''
              const hashtags: string[] = post.hashtags || contentApi.data.hashtags || []
              const charCount: number = post.char_count || postText.length
              return (
                <Card style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                    <Badge text={platform.toUpperCase()} color="blue" />
                    <Badge text={tone} color="purple" />
                    
                  </div>
                  {postText && (
                    <div style={{ background: '#0f1117', borderRadius: 8, padding: 16, marginBottom: 10 }}>
                      <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{postText}</div>
                      <div style={{ marginTop: 8, color: '#6b7280', fontSize: 11 }}>{charCount} / {post.max_chars || 3000} characters</div>
                    </div>
                  )}
                  {hashtags.length > 0 && (
                    <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                      {hashtags.slice(0, 8).map((h: string) => (
                        <span key={h} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 20, background: 'rgba(16,185,129,0.15)', color: '#5eead4' }}>
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
                      background: i < 5 ? 'rgba(16,185,129,0.2)' : 'rgba(34,197,94,0.1)',
                      color: i < 5 ? '#5eead4' : '#86efac',
                      border: `1px solid ${i < 5 ? 'rgba(16,185,129,0.3)' : 'rgba(34,197,94,0.2)'}`,
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
            <SectionHead title="AI Image Generation" sub="AI-generated 1024×1024 images for your posts" />
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
                  AI-generated image • 1024×1024
                </div>
              </Card>
            )}
            <ResultBox data={imgApi.data} loading={imgApi.loading} error={imgApi.error} title="Image Response" />
          </div>
        </TwoCol>
      )}

      {/* ── SEO Audit ── */}
      {tab === 'seo' && (
        <TwoCol>
          <Card>
            <SectionHead title="SEO Audit" sub="Technical SEO, on-page analysis, keyword gaps, and 30-60-90 day roadmap" />
            <Input label="Page URL"               value={seoUrl}         onChange={setSeoUrl} />
            <Input label="Target Keywords"        value={seoKeywords}    onChange={setSeoKeywords} rows={2} />
            <Input label="Competitor Sites"       value={seoCompetitors} onChange={setSeoCompetitors} />
            <Input label="Page Content (optional, helps with analysis)" value={seoContent} onChange={setSeoContent} rows={5}
              placeholder="Paste page content or meta description..." />
            <div style={{ padding: 10, background: 'rgba(16,185,129,0.08)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#5eead4', marginBottom: 4 }}>🔍 Audit covers</div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>Technical SEO checklist (20 items) • On-page score • Content gaps • Core Web Vitals • Meta tag templates • 30-60-90 day roadmap</div>
            </div>
            <Btn
              onClick={() => seoApi.call(() => socialEnhance('seo_audit', {
                url:              seoUrl,
                target_keywords:  seoKeywords,
                competitors:      seoCompetitors,
                page_content:     seoContent,
              }))}
              loading={seoApi.loading}
            >
              🔍 Run SEO Audit
            </Btn>
          </Card>
          <ResultBox data={seoApi.data ? { audit: (seoApi.data as any).result } : null} loading={seoApi.loading} error={seoApi.error} title="SEO Audit Report" />
        </TwoCol>
      )}

      {/* ── Campaign Brief ── */}
      {tab === 'campaign' && (
        <TwoCol>
          <Card>
            <SectionHead title="Marketing Campaign Brief" sub="Full campaign strategy with audience personas, channel mix, KPIs, and content calendar" />
            <Input label="Product / Service"    value={campProduct}   onChange={setCampProduct} />
            <Input label="Target Audience"      value={campAudience}  onChange={setCampAudience} rows={2} />
            <Input label="Budget"               value={campBudget}    onChange={setCampBudget} />
            <Input label="Timeline"             value={campTimeline}  onChange={setCampTimeline} />
            <Input label="Channels"             value={campChannels}  onChange={setCampChannels} />
            <Input label="Primary Goal / KPI"   value={campGoal}      onChange={setCampGoal} rows={2} />
            <Btn
              onClick={() => campaignApi.call(() => socialEnhance('campaign_brief', {
                product:         campProduct,
                target_audience: campAudience,
                budget:          campBudget,
                timeline:        campTimeline,
                channels:        campChannels,
                goal:            campGoal,
              }))}
              loading={campaignApi.loading}
            >
              📋 Generate Campaign Brief
            </Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Brief Includes" sub="" />
              {['Campaign theme + tagline','3 audience personas','Messaging hierarchy','Channel budget allocation %','4-week content calendar','KPIs + targets','A/B test plan','Creative brief summary'].map(i => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: '1px solid #1e2535' }}>
                  <span style={{ color: '#22c55e', fontSize: 12 }}>✓</span>
                  <span style={{ color: '#9ca3af', fontSize: 12 }}>{i}</span>
                </div>
              ))}
            </Card>
            <ResultBox data={campaignApi.data ? { brief: (campaignApi.data as any).result } : null} loading={campaignApi.loading} error={campaignApi.error} title="Campaign Brief" />
          </div>
        </TwoCol>
      )}
    </PageShell>
  )
}
