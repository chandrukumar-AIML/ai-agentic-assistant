// frontend/src/pages/SocialPage.tsx — AI Social Media Manager (Enterprise Depth)
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { generateContent, generateHashtags, generateImage, socialEnhance, socialPro, submitSocialForApproval, socialAction } from '../lib/api'

const PLATFORMS  = [{ label: 'LinkedIn', value: 'linkedin' }, { label: 'Twitter/X', value: 'twitter' }, { label: 'Instagram', value: 'instagram' }, { label: 'Facebook', value: 'facebook' }]
const TONES      = [{ label: 'Professional', value: 'professional' }, { label: 'Casual', value: 'casual' }, { label: 'Inspirational', value: 'inspirational' }, { label: 'Educational', value: 'educational' }, { label: 'Humorous', value: 'humorous' }]
const AD_PLATFORMS = [{ label: 'Meta (Facebook/Instagram)', value: 'meta' }, { label: 'Google Ads', value: 'google' }, { label: 'LinkedIn Ads', value: 'linkedin' }, { label: 'YouTube Ads', value: 'youtube' }]
const AD_GOALS   = [{ label: 'Lead Generation', value: 'leads' }, { label: 'Awareness', value: 'awareness' }, { label: 'Clicks / Traffic', value: 'clicks' }, { label: 'Conversions / Sales', value: 'conversions' }]
const CRISIS_TYPES = [{ label: 'Negative Review Going Viral', value: 'negative_review' }, { label: 'Product/Service Issue', value: 'product_issue' }, { label: 'PR Controversy', value: 'pr_controversy' }, { label: 'Data Breach', value: 'data_breach' }, { label: 'Employee Misconduct', value: 'employee_misconduct' }]
const SEVERITY   = [{ label: 'Low', value: 'low' }, { label: 'Medium', value: 'medium' }, { label: 'High', value: 'high' }, { label: 'Critical', value: 'critical' }]
const YT_STYLES  = [{ label: 'Educational / How-To', value: 'educational' }, { label: 'Tutorial', value: 'tutorial' }, { label: 'Product Review', value: 'review' }, { label: 'Vlog / Behind the Scenes', value: 'vlog' }, { label: 'YouTube Shorts', value: 'shorts' }]
const SEQ_TYPES  = [{ label: 'Welcome Series', value: 'welcome' }, { label: 'Drip / Nurture', value: 'drip' }, { label: 'Re-engagement', value: 're_engagement' }, { label: 'Product Launch', value: 'product_launch' }, { label: 'Post-Purchase', value: 'post_purchase' }]
const HOOK_STYLES = [{ label: 'Bold Question', value: 'question' }, { label: 'Shocking Statistic', value: 'stat' }, { label: 'Bold Claim', value: 'bold_claim' }, { label: 'Story Opening', value: 'story' }, { label: 'Listicle Hook', value: 'listicle' }]
const REEL_DURS  = [{ label: '15 seconds', value: 15 }, { label: '30 seconds', value: 30 }, { label: '60 seconds', value: 60 }]
const CONTENT_TYPES = [{ label: 'Blog Post', value: 'blog' }, { label: 'Article', value: 'article' }, { label: 'Podcast Episode', value: 'podcast' }, { label: 'Video Transcript', value: 'video' }]

const TOPICS = ['AI in Healthcare India', 'Startup funding tips', 'Python best practices', 'Climate change solutions', 'Digital marketing trends']
const REGIONAL_LANGS = [{ label: 'Tamil (தமிழ்)', value: 'tamil' }, { label: 'Hindi (हिन्दी)', value: 'hindi' }, { label: 'Telugu (తెలుగు)', value: 'telugu' }, { label: 'Kannada (ಕನ್ನಡ)', value: 'kannada' }, { label: 'Malayalam (മലയാളം)', value: 'malayalam' }, { label: 'Marathi (मराठी)', value: 'marathi' }]
const WA_TYPES = [{ label: 'Broadcast / Promo', value: 'broadcast' }, { label: 'Product Catalogue', value: 'catalogue' }, { label: 'Welcome Message', value: 'welcome' }, { label: 'Abandoned Cart Recovery', value: 'abandoned_cart' }, { label: 'Review Request', value: 'review_request' }, { label: 'Reorder Reminder', value: 'reorder' }]
const CAL_TONES = [{ label: 'Festive', value: 'festive' }, { label: 'Professional', value: 'professional' }, { label: 'Emotional / Heartfelt', value: 'emotional' }, { label: 'Humorous', value: 'humorous' }]
const LANG_OPTIONS = [{ label: 'English', value: 'en' }, { label: 'Tamil', value: 'tamil' }, { label: 'Hindi', value: 'hindi' }, { label: 'Telugu', value: 'telugu' }]
const CAL_PLATFORMS = ['instagram', 'linkedin', 'twitter', 'whatsapp', 'facebook']
const NICHES = [{ label: 'CA / Chartered Accountant Firm', value: 'ca_firm' }, { label: 'Legal Firm / Lawyer', value: 'legal_firm' }, { label: 'Medical Clinic / Hospital', value: 'clinic' }, { label: 'School / Coaching', value: 'school' }, { label: 'Restaurant / Food', value: 'restaurant' }, { label: 'Real Estate', value: 'real_estate' }, { label: 'Salon / Beauty', value: 'salon' }]
const TRIGGER_TYPES = [{ label: 'CRM Deal Won 🎉', value: 'crm_deal_won' }, { label: 'New Team Hire 👋', value: 'hr_hire' }, { label: 'Product Launch 🚀', value: 'product_launch' }, { label: 'Company Milestone 🏆', value: 'milestone' }, { label: 'Event / Webinar 📅', value: 'event' }, { label: 'Award / Recognition 🥇', value: 'award' }, { label: 'Client Success Story ⭐', value: 'client_success' }]
const POST_STATUSES = ['Draft', 'Scheduled', 'Posted', 'Failed'] as const
type PostStatus = typeof POST_STATUSES[number]
interface QueuePost { id: string; topic: string; platform: string; text: string; status: PostStatus; createdAt: string; scheduledFor?: string }
const STATUS_COLORS: Record<PostStatus, string> = { Draft: '#6b7280', Scheduled: '#3b82f6', Posted: '#22c55e', Failed: '#ef4444' }

export default function SocialPage() {
  const [tab, setTab] = useState('content')

  // ── Tab 1: Content Generator ──
  const [topic, setTopic]       = useState(TOPICS[0])
  const [platform, setPlatform] = useState('linkedin')
  const [tone, setTone]         = useState('professional')
  const contentApi = useApi()

  // ── Tab 2: Hashtags ──
  const [hashTopic, setHashTopic] = useState('AI startups India')
  const [hashPlat, setHashPlat]   = useState('instagram')
  const hashApi = useApi()
  const [hashHistory, setHashHistory] = useState<{ topic: string; platform: string; tags: string[]; date: string }[]>(() => {
    try { return JSON.parse(localStorage.getItem('social_hashtag_history') || '[]') } catch { return [] }
  })
  const saveHashHistory = (topic: string, platform: string, tags: string[]) => {
    const entry = { topic, platform, tags, date: new Date().toISOString() }
    const next = [entry, ...hashHistory].slice(0, 20)
    setHashHistory(next)
    localStorage.setItem('social_hashtag_history', JSON.stringify(next))
  }

  // ── Tab 3: AI Image ──
  const [imgPrompt, setImgPrompt] = useState('Modern AI technology with Indian corporate professionals')
  const imgApi = useApi()

  // ── Tab 4: SEO Audit ──
  const [seoUrl, setSeoUrl]             = useState('https://yourdomain.com/product')
  const [seoKeywords, setSeoKeywords]   = useState('AI platform India, enterprise automation, B2B SaaS India')
  const [seoCompetitors, setSeoCompetitors] = useState('competitor1.com, competitor2.com')
  const [seoContent, setSeoContent]     = useState('')
  const seoApi = useApi()

  // ── Tab 5: Campaign Brief ──
  const [campProduct, setCampProduct]   = useState('AI Agentic Platform — Enterprise Edition')
  const [campAudience, setCampAudience] = useState('CTOs and VP Engineering at 200–2000 employee tech companies in India')
  const [campBudget, setCampBudget]     = useState('₹5,00,000 / month')
  const [campTimeline, setCampTimeline] = useState('3 months (Q1 2026)')
  const [campChannels, setCampChannels] = useState('LinkedIn Ads, Google Search, Email nurture, Content marketing')
  const [campGoal, setCampGoal]         = useState('Generate 50 qualified leads per month at CPL < ₹10,000')
  const campaignApi = useApi()

  // ── Tab 6: Content Repurposing ──
  const [repContent, setRepContent]     = useState('')
  const [repType, setRepType]           = useState('blog')
  const [repBrand, setRepBrand]         = useState('')
  const [repTone, setRepTone]           = useState('professional')
  const repApi = useApi()

  // ── Tab 7: Competitor Audit ──
  const [compName, setCompName]         = useState('')
  const [compNiche, setCompNiche]       = useState('')
  const [compOurBrand, setCompOurBrand] = useState('')
  const compApi = useApi()

  // ── Tab 8: Ad Copy Generator ──
  const [adProduct, setAdProduct]       = useState('')
  const [adAudience, setAdAudience]     = useState('')
  const [adGoal, setAdGoal]             = useState('leads')
  const [adPlatform, setAdPlatform]     = useState('meta')
  const [adUSP, setAdUSP]               = useState('')
  const [adBudget, setAdBudget]         = useState('')
  const adApi = useApi()

  // ── Tab 9: Influencer Brief ──
  const [infBrand, setInfBrand]         = useState('')
  const [infProduct, setInfProduct]     = useState('')
  const [infGoal, setInfGoal]           = useState('')
  const [infNiche, setInfNiche]         = useState('')
  const [infDeliverables, setInfDeliverables] = useState('2 Instagram Reels, 3 Stories, 1 YouTube integration')
  const [infBudget, setInfBudget]       = useState('₹50,000 per influencer')
  const [infTimeline, setInfTimeline]   = useState('4 weeks')
  const [infDosDonts, setInfDosDonts]   = useState('')
  const infApi = useApi()

  // ── Tab 10: Crisis Response ──
  const [crisBrand, setCrisBrand]       = useState('')
  const [crisType, setCrisType]         = useState('negative_review')
  const [crisDetail, setCrisDetail]     = useState('')
  const [crisSeverity, setCrisSeverity] = useState('medium')
  const crisApi = useApi()

  // ── Tab 11: YouTube Script ──
  const [ytTopic, setYtTopic]           = useState('')
  const [ytNiche, setYtNiche]           = useState('')
  const [ytDuration, setYtDuration]     = useState(8)
  const [ytStyle, setYtStyle]           = useState('educational')
  const [ytBrand, setYtBrand]           = useState('')
  const [ytCta, setYtCta]               = useState('Subscribe and hit the bell icon')
  const ytApi = useApi()

  // ── Tab 12: Email Sequence ──
  const [emailProduct, setEmailProduct] = useState('')
  const [emailAudience, setEmailAudience] = useState('')
  const [emailType, setEmailType]       = useState('welcome')
  const [emailCount, setEmailCount]     = useState(5)
  const [emailBrand, setEmailBrand]     = useState('')
  const [emailTone, setEmailTone]       = useState('friendly')
  const emailApi = useApi()

  // ── Tab 13: Reel Script ──
  const [reelTopic, setReelTopic]       = useState('')
  const [reelDuration, setReelDuration] = useState(30)
  const [reelPlatform, setReelPlatform] = useState('instagram')
  const [reelHook, setReelHook]         = useState('question')
  const [reelBrand, setReelBrand]       = useState('')
  const reelApi = useApi()

  // ── Tab 14: Monthly Report ──
  const [repBrandName, setRepBrandName]   = useState('')
  const [repMonth, setRepMonth]           = useState('June 2026')
  const [repGoals, setRepGoals]           = useState('')
  const [repFollowers, setRepFollowers]   = useState('')
  const [repPosts, setRepPosts]           = useState('')
  const [repReach, setRepReach]           = useState('')
  const [repEngagement, setRepEngagement] = useState('')
  const reportApi = useApi()

  // ── Tab 15: Keyword Cluster ──
  const [kwTopic, setKwTopic]     = useState('')
  const [kwIndustry, setKwIndustry] = useState('')
  const [kwAudience, setKwAudience] = useState('')
  const [kwMarket, setKwMarket]   = useState('India')
  const kwApi = useApi()

  // ── Tab 16: Brand Kit ──
  const [bkBrand, setBkBrand]       = useState('')
  const [bkIndustry, setBkIndustry] = useState('')
  const [bkAudience, setBkAudience] = useState('')
  const [bkTone, setBkTone]         = useState('professional')
  const [bkPillars, setBkPillars]   = useState('')
  const bkApi = useApi()

  // ── Tab 17: Bulk Generator ──
  const [bulkTopics, setBulkTopics] = useState('AI tools for SMBs\nGST tips for businesses\nSocial media marketing India\nStartup growth hacks\nProductivity with AI\nCustomer retention strategies\nDigital India trends')
  const [bulkPlatform, setBulkPlatform] = useState('linkedin')
  const [bulkTone, setBulkTone]     = useState('professional')
  const [bulkBrand, setBulkBrand]   = useState('')
  const bulkApi = useApi()

  // ── Tab 18: Analytics ──
  const [anlPlatform, setAnlPlatform] = useState('linkedin')
  const [anlIndustry, setAnlIndustry] = useState('')
  const [anlAudience, setAnlAudience] = useState('')
  const [anlRate, setAnlRate]         = useState('3.5')
  const [anlFollowers, setAnlFollowers] = useState('')
  const [anlPostText, setAnlPostText] = useState('')
  const timeApi = useApi()
  const benchApi = useApi()
  const scoreApi = useApi()

  // ── Tab 19: India & WhatsApp ──
  const [indIndustry, setIndIndustry]   = useState('')
  const [indRegLang, setIndRegLang]     = useState('tamil')
  const [indRegTopic, setIndRegTopic]   = useState('')
  const [indRegBrand, setIndRegBrand]   = useState('')
  const [waTopic, setWaTopic]           = useState('')
  const [waType, setWaType]             = useState('broadcast')
  const [waBrand, setWaBrand]           = useState('')
  const [waProduct, setWaProduct]       = useState('')
  const [waOffer, setWaOffer]           = useState('')
  const [waIndustry, setWaIndustry]     = useState('')
  const trendApi    = useApi()
  const regionalApi = useApi()
  const waApi       = useApi()

  // ── Cultural Calendar ──
  const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']
  const [calBrandName, setCalBrandName]   = useState('')
  const [calIndustryCC, setCalIndustryCC] = useState('')
  const [calSelectedMonths, setCalSelectedMonths] = useState<string[]>([])
  const [calPlatforms, setCalPlatforms]   = useState<string[]>(['instagram', 'whatsapp'])
  const [calTone, setCalTone]             = useState('festive')
  const [calLang, setCalLang]             = useState('en')
  const culturalApi = useApi()
  const toggleMonth = (m: string) => setCalSelectedMonths(prev => prev.includes(m) ? prev.filter(x => x !== m) : [...prev, m])
  const togglePlatform = (p: string) => setCalPlatforms(prev => prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p])

  // ── Tab 20: Niche Templates ──
  const [ntNiche, setNtNiche]   = useState('ca_firm')
  const [ntBrand, setNtBrand]   = useState('')
  const [ntMonth, setNtMonth]   = useState('')
  const ntApi = useApi()

  // ── Tab 21: Calendar & Queue ──
  const [calBrand, setCalBrand]       = useState('')
  const [calIndustry, setCalIndustry] = useState('')
  const [calDays, setCalDays]         = useState(7)
  const [calPlats, setCalPlats]       = useState('linkedin,twitter')
  const [queue, setQueue]             = useState<QueuePost[]>(() => {
    try { return JSON.parse(localStorage.getItem('social_post_queue') || '[]') } catch { return [] }
  })
  const calApi = useApi()

  const saveQueue = (q: QueuePost[]) => { setQueue(q); localStorage.setItem('social_post_queue', JSON.stringify(q)) }
  const addToQueue = (post: Omit<QueuePost, 'id' | 'createdAt' | 'status'>) => {
    const newPost: QueuePost = { ...post, id: Date.now().toString(), createdAt: new Date().toISOString(), status: 'Draft' }
    saveQueue([newPost, ...queue])
  }
  const updateStatus = (id: string, status: PostStatus) => saveQueue(queue.map(p => p.id === id ? { ...p, status } : p))
  const removeFromQueue = (id: string) => saveQueue(queue.filter(p => p.id !== id))

  // ── Tab 22: Monitor ──
  const [monBrand, setMonBrand]       = useState('')
  const [monIndustry, setMonIndustry] = useState('')
  const [monCompetitors, setMonCompetitors] = useState('')
  const [ctrCompName, setCtrCompName] = useState('')
  const [ctrNiche, setCtrNiche]       = useState('')
  const [ctrOurBrand, setCtrOurBrand] = useState('')
  const [uaBrand, setUaBrand]         = useState('')
  const [uaPeriod, setUaPeriod]       = useState('last_month')
  const [uaLI, setUaLI]               = useState('')
  const [uaTW, setUaTW]               = useState('')
  const [uaIG, setUaIG]               = useState('')
  const monitorApi = useApi()
  const ctrApi     = useApi()
  const uaApi      = useApi()

  // ── Tab 23: Bridge ──
  const [bridgeTrigger, setBridgeTrigger] = useState('crm_deal_won')
  const [bridgePlatform, setBridgePlatform] = useState('linkedin')
  const [bridgeBrand, setBridgeBrand]   = useState('')
  const [bridgeTone, setBridgeTone]     = useState('professional')
  const [bridgeClient, setBridgeClient] = useState('')
  const [bridgeValue, setBridgeValue]   = useState('')
  const [bridgeRole, setBridgeRole]     = useState('')
  const [bridgeDept, setBridgeDept]     = useState('')
  const [bridgeProduct, setBridgeProduct] = useState('')
  const [bridgeMilestone, setBridgeMilestone] = useState('')
  const [bridgeEventName, setBridgeEventName] = useState('')
  const [bridgeAward, setBridgeAward]   = useState('')
  const [bridgeResult, setBridgeResult] = useState('')
  const bridgeApi = useApi()

  // ── A/B Copy Tester (Round 5) ──
  const [abTopic, setAbTopic]       = useState('')
  const [abBrand, setAbBrand]       = useState('')
  const [abIndustry, setAbIndustry] = useState('')
  const [abPlatform, setAbPlatform] = useState('linkedin')
  const [abGoal, setAbGoal]         = useState('engagement')
  const [abVariations, setAbVariations] = useState('4')
  const [abRes, setAbRes]           = useState<any>(null)
  const [abLoading, setAbLoading]   = useState(false)
  const [abErr, setAbErr]           = useState('')
  const [abSelected, setAbSelected] = useState<number | null>(null)

  const runAbTest = async () => {
    setAbLoading(true); setAbErr(''); setAbRes(null); setAbSelected(null)
    try {
      setAbRes(await socialAction('ab_copy_test', {
        topic: abTopic, brand_name: abBrand, industry: abIndustry,
        goal: abGoal, variations: parseInt(abVariations),
      }, abPlatform))
    } catch (e: any) { setAbErr(e.message) }
    setAbLoading(false)
  }

  // ── AI Content Scheduler (Round 4) ──
  const [schBrand, setSchBrand]       = useState('')
  const [schIndustry, setSchIndustry] = useState('')
  const [schDays, setSchDays]         = useState('7')
  const [schGoal, setSchGoal]         = useState('brand awareness')
  const [schAudience, setSchAudience] = useState('small business owners')
  const [schPlatforms, setSchPlatforms] = useState<string[]>(['instagram', 'linkedin'])
  const [schRes, setSchRes]           = useState<any>(null)
  const [schLoading, setSchLoading]   = useState(false)
  const [schErr, setSchErr]           = useState('')
  const [schExpandDay, setSchExpandDay] = useState<number | null>(0)

  const toggleSchPlatform = (p: string) =>
    setSchPlatforms(prev => prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p])

  const runScheduler = async () => {
    setSchLoading(true); setSchErr(''); setSchRes(null)
    try {
      setSchRes(await socialAction('content_scheduler', {
        brand_name: schBrand, industry: schIndustry,
        platforms: schPlatforms, days: parseInt(schDays),
        goal: schGoal, audience: schAudience,
      }))
      setSchExpandDay(0)
    } catch (e: any) { setSchErr(e.message) }
    setSchLoading(false)
  }

  // ── Preview state (enhancement to Content tab) ──
  const [previewText, setPreviewText] = useState('')
  const [previewPlatform, setPreviewPlatform] = useState('linkedin')
  const previewApi = useApi()

  // ── Feature 20: Team Approval ──
  const [approvalId, setApprovalId] = useState('')
  const [approvalLoading, setApprovalLoading] = useState(false)
  const submitForApproval = async (postText: string, postPlatform: string, postTopic: string) => {
    setApprovalLoading(true)
    try {
      const res: any = await submitSocialForApproval(postText, postPlatform, postTopic)
      setApprovalId(res.approval_id || '')
    } catch { setApprovalId('') } finally { setApprovalLoading(false) }
  }

  // ── Feature 25: Calendar Repurpose ──
  const [repurposeResults, setRepurposeResults] = useState<Record<number, string>>({})
  const [repurposeLoading, setRepurposeLoading] = useState<Record<number, boolean>>({})
  const repurposeCalItem = async (index: number, brief: string) => {
    setRepurposeLoading(r => ({ ...r, [index]: true }))
    try {
      const res: any = await socialPro('repurpose', { source_content: brief, content_type: 'social_post', brand_name: calBrand })
      const formats = res?.formats || {}
      const text = formats.linkedin_post || formats.twitter_thread || formats.instagram_caption || JSON.stringify(res)
      setRepurposeResults(r => ({ ...r, [index]: text }))
    } catch { setRepurposeResults(r => ({ ...r, [index]: 'Error repurposing content' })) }
    finally { setRepurposeLoading(r => ({ ...r, [index]: false })) }
  }

  return (
    <PageShell icon="📱" title="AI Social Media Manager" subtitle="Content · Ads · Influencer · Crisis · YouTube · Email · Reels · SEO — Enterprise depth">
      <Tabs
        tabs={[
          { id: 'content',    label: 'Content',       icon: '✍️' },
          { id: 'hashtags',   label: 'Hashtags',      icon: '#️⃣' },
          { id: 'image',      label: 'AI Image',      icon: '🎨' },
          { id: 'repurpose',  label: 'Repurpose',     icon: '♻️' },
          { id: 'competitor', label: 'Competitor',    icon: '🔎' },
          { id: 'adcopy',     label: 'Ad Copy',       icon: '📣' },
          { id: 'influencer', label: 'Influencer',    icon: '🤝' },
          { id: 'crisis',     label: 'Crisis',        icon: '🚨' },
          { id: 'youtube',    label: 'YouTube',       icon: '▶️' },
          { id: 'email',      label: 'Email Sequence',icon: '📧' },
          { id: 'reel',       label: 'Reel Script',   icon: '🎬' },
          { id: 'report',     label: 'Monthly Report',icon: '📊' },
          { id: 'kwcluster',  label: 'SEO Cluster',   icon: '🔍' },
          { id: 'seo',        label: 'SEO Audit',     icon: '📈' },
          { id: 'campaign',   label: 'Campaign Brief', icon: '📋' },
          { id: 'brandkit',   label: 'Brand Kit',      icon: '🏷️' },
          { id: 'bulk',       label: 'Bulk Generate',  icon: '⚡' },
          { id: 'analytics',  label: 'Analytics',      icon: '📉' },
          { id: 'india',      label: 'India & WhatsApp', icon: '🇮🇳' },
          { id: 'templates',  label: 'Niche Templates', icon: '🗂️' },
          { id: 'calendar',   label: 'Calendar & Queue', icon: '📅' },
          { id: 'monitor',    label: 'Monitor',         icon: '👁️' },
          { id: 'bridge',     label: 'Content Bridge',  icon: '🔗' },
          { id: 'scheduler',  label: 'AI Scheduler',    icon: '🗓️' },
          { id: 'abtest',     label: 'A/B Copy Tester', icon: '🔬' },
        ]}
        active={tab} onChange={setTab}
      />

      {/* ── CONTENT GENERATOR ── */}
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
              const postError = post.error || contentApi.data.error || ''
              const hashtags: string[] = post.hashtags || []
              return (
                <Card style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                    <Badge text={platform.toUpperCase()} color="blue" />
                    <Badge text={tone} color="purple" />
                  </div>
                  {postError && (
                    <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: 12, marginBottom: 10, color: '#f87171', fontSize: 13 }}>
                      ⚠️ {postError}
                    </div>
                  )}
                  {postText && (
                    <div style={{ background: '#0f1117', borderRadius: 8, padding: 16, marginBottom: 10 }}>
                      <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{postText}</div>
                      <div style={{ marginTop: 8, color: '#6b7280', fontSize: 11 }}>{post.char_count || postText.length} / {post.max_chars || 3000} chars</div>
                    </div>
                  )}
                  {hashtags.length > 0 && (
                    <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginBottom: 10 }}>
                      {hashtags.slice(0, 8).map((h: string) => (
                        <span key={h} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 20, background: 'rgba(16,185,129,0.15)', color: '#5eead4' }}>
                          {h.startsWith('#') ? h : `#${h}`}
                        </span>
                      ))}
                    </div>
                  )}
                  {postText && (
                    <div style={{ borderTop: '1px solid #1e2535', paddingTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      <Btn onClick={() => submitForApproval(postText, platform, topic)} loading={approvalLoading} style={{ fontSize: 11, padding: '4px 10px' }}>
                        📤 Submit for Team Review
                      </Btn>
                      {approvalId && (
                        <div style={{ fontSize: 11, color: '#22c55e', padding: '4px 10px', background: 'rgba(34,197,94,0.1)', borderRadius: 6, border: '1px solid rgba(34,197,94,0.3)' }}>
                          ✅ Submitted — ID: {approvalId}
                        </div>
                      )}
                    </div>
                  )}
                </Card>
              )
            })()}
            <ResultBox data={contentApi.data} loading={contentApi.loading} error={contentApi.error} title="Generated Content" />
          </div>
        </TwoCol>
      )}

      {/* ── HASHTAGS ── */}
      {tab === 'hashtags' && (
        <TwoCol>
          <Card>
            <SectionHead title="Hashtag Research" sub="Trending + niche hashtags for maximum reach" />
            <Select label="Platform" value={hashPlat} onChange={setHashPlat} options={PLATFORMS} />
            <Input label="Topic" value={hashTopic} onChange={setHashTopic} />
            <Btn onClick={async () => {
              await hashApi.call(() => generateHashtags(hashTopic, hashPlat))
            }} loading={hashApi.loading}>
              #️⃣ Find Hashtags
            </Btn>
          </Card>
          <div>
            {hashApi.data?.hashtags && (() => {
              const tags: string[] = hashApi.data.hashtags
              return (
                <Card style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                    <SectionHead title="Recommended Hashtags" />
                    <Btn onClick={() => saveHashHistory(hashTopic, hashPlat, tags)} style={{ padding: '3px 10px', fontSize: 11 }}>
                      💾 Save to History
                    </Btn>
                  </div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {tags.map((h: string, i: number) => (
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
              )
            })()}
            {hashHistory.length > 0 && (
              <Card style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <SectionHead title="📚 Hashtag History" sub={`${hashHistory.length} saved sets`} />
                  <button onClick={() => { setHashHistory([]); localStorage.removeItem('social_hashtag_history') }}
                    style={{ background: 'none', border: 'none', color: '#ef4444', fontSize: 11, cursor: 'pointer' }}>
                    🗑️ Clear All
                  </button>
                </div>
                {hashHistory.map((entry, i) => (
                  <div key={i} style={{ padding: '8px 10px', marginBottom: 6, borderRadius: 6, background: '#0f1117', border: '1px solid #1e2535', cursor: 'pointer' }}
                    onClick={() => { setHashTopic(entry.topic); setHashPlat(entry.platform) }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ color: '#5eead4', fontSize: 12, fontWeight: 600 }}>{entry.topic}</span>
                      <span style={{ color: '#4b5563', fontSize: 10 }}>{new Date(entry.date).toLocaleDateString()}</span>
                    </div>
                    <div style={{ color: '#6b7280', fontSize: 11 }}>{entry.platform.toUpperCase()} • {entry.tags.slice(0, 5).map(t => t.startsWith('#') ? t : `#${t}`).join(' ')}</div>
                  </div>
                ))}
              </Card>
            )}
            <ResultBox data={hashApi.data} loading={hashApi.loading} error={hashApi.error} title="Hashtag Data" />
          </div>
        </TwoCol>
      )}

      {/* ── AI IMAGE ── */}
      {tab === 'image' && (
        <TwoCol>
          <Card>
            <SectionHead title="AI Image Generation" sub="DALL-E 3 visuals optimized per platform" />
            <Input label="Image Prompt" value={imgPrompt} onChange={setImgPrompt} rows={3} />
            {['Modern AI technology with Indian corporate professionals', 'Vibrant startup ecosystem in Bengaluru', 'Digital transformation in Indian agriculture'].map(p => (
              <button key={p} onClick={() => setImgPrompt(p)} style={{
                display: 'block', width: '100%', textAlign: 'left', padding: '6px 10px', marginBottom: 4,
                background: '#0f1117', border: '1px solid #1e2535', borderRadius: 6, color: '#6b7280', fontSize: 11, cursor: 'pointer',
              }}>{p}</button>
            ))}
            <Btn onClick={() => imgApi.call(() => generateImage(imgPrompt))} loading={imgApi.loading}>🎨 Generate Image</Btn>
          </Card>
          <div>
            {imgApi.data?.image_url && (
              <Card style={{ marginBottom: 12 }}>
                <img src={imgApi.data.image_url} alt="Generated" style={{ width: '100%', borderRadius: 8 }} />
              </Card>
            )}
            <ResultBox data={imgApi.data} loading={imgApi.loading} error={imgApi.error} title="Image Response" />
          </div>
        </TwoCol>
      )}

      {/* ── CONTENT REPURPOSING ── */}
      {tab === 'repurpose' && (
        <TwoCol>
          <Card>
            <SectionHead title="Content Repurposing Engine" sub="One piece of content → 6 platform-ready formats instantly" />
            <Select label="Content Type" value={repType} onChange={setRepType} options={CONTENT_TYPES} />
            <Select label="Tone"         value={repTone} onChange={setRepTone} options={TONES} />
            <Input  label="Brand Name (optional)" value={repBrand} onChange={setRepBrand} />
            <Input  label="Paste your blog / article / script here" value={repContent} onChange={setRepContent} rows={10}
              placeholder="Paste your full blog post, article, or script here..." />
            <div style={{ padding: 10, background: 'rgba(16,185,129,0.07)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#5eead4', marginBottom: 4 }}>♻️ Generates all at once</div>
              {['LinkedIn long-form post', 'Twitter thread (3 tweets)', 'Instagram caption', 'Email subject + preview', 'YouTube description', '3 pull quotes'].map(f => (
                <div key={f} style={{ display: 'flex', gap: 6, padding: '2px 0' }}>
                  <span style={{ color: '#22c55e', fontSize: 11 }}>✓</span>
                  <span style={{ color: '#6b7280', fontSize: 11 }}>{f}</span>
                </div>
              ))}
            </div>
            <Btn onClick={() => repApi.call(() => socialPro('repurpose', {
              source_content: repContent, content_type: repType, brand_name: repBrand, tone: repTone,
            }))} loading={repApi.loading}>♻️ Repurpose Content</Btn>
          </Card>
          <div>
            {repApi.data?.formats && !repApi.loading && (() => {
              const f = repApi.data.formats
              return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {f.linkedin_post && <Card><SectionHead title="LinkedIn Post" /><div style={{ color: '#e2e8f0', fontSize: 12, whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{f.linkedin_post}</div></Card>}
                  {f.twitter_thread && <Card><SectionHead title="Twitter Thread" />
                    {(Array.isArray(f.twitter_thread) ? f.twitter_thread : [f.twitter_thread]).map((t: string, i: number) => (
                      <div key={i} style={{ padding: '8px 0', borderBottom: '1px solid #1e2535', color: '#e2e8f0', fontSize: 12 }}>{i + 1}/ {t}</div>
                    ))}
                  </Card>}
                  {f.instagram_caption && <Card><SectionHead title="Instagram Caption" /><div style={{ color: '#e2e8f0', fontSize: 12, whiteSpace: 'pre-wrap' }}>{f.instagram_caption}</div></Card>}
                  {f.email_subject_and_preview && <Card><SectionHead title="Email Subject + Preview" /><div style={{ color: '#e2e8f0', fontSize: 12 }}>{f.email_subject_and_preview}</div></Card>}
                  {f.key_quotes && <Card><SectionHead title="Pull Quotes" />
                    {(Array.isArray(f.key_quotes) ? f.key_quotes : [f.key_quotes]).map((q: string, i: number) => (
                      <div key={i} style={{ padding: '6px 12px', borderLeft: '3px solid #3b82f6', margin: '6px 0', color: '#94a3b8', fontSize: 12, fontStyle: 'italic' }}>"{q}"</div>
                    ))}
                  </Card>}
                  {f.raw_output && <ResultBox data={{ output: f.raw_output }} loading={false} error={undefined} title="Repurposed Output" />}
                </div>
              )
            })()}
            {!repApi.data && <ResultBox data={null} loading={repApi.loading} error={repApi.error} title="Repurposed Formats" />}
          </div>
        </TwoCol>
      )}

      {/* ── COMPETITOR AUDIT ── */}
      {tab === 'competitor' && (
        <TwoCol>
          <Card>
            <SectionHead title="Competitor Social Audit" sub="Analyze their strategy, find gaps, build your counter-play" />
            <Input label="Competitor Name"  value={compName}     onChange={setCompName}     placeholder="e.g. Zoho, HubSpot, Freshworks" />
            <Input label="Their Niche"      value={compNiche}    onChange={setCompNiche}    placeholder="e.g. B2B SaaS, CRM, India SMB market" />
            <Input label="Our Brand Name"   value={compOurBrand} onChange={setCompOurBrand} placeholder="Your brand (for counter-strategy)" />
            <div style={{ padding: 10, background: 'rgba(59,130,246,0.07)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#60a5fa', marginBottom: 4 }}>🔎 Audit covers</div>
              {['Posting frequency estimate','Content type breakdown','Tone & messaging style','Hashtag strategy','Engagement tactics','Their gaps & weaknesses','Content angles they miss','5-point counter-strategy for you'].map(f => (
                <div key={f} style={{ display: 'flex', gap: 6, padding: '2px 0' }}>
                  <span style={{ color: '#3b82f6', fontSize: 11 }}>→</span>
                  <span style={{ color: '#6b7280', fontSize: 11 }}>{f}</span>
                </div>
              ))}
            </div>
            <Btn onClick={() => compApi.call(() => socialPro('competitor_audit', {
              competitor_name: compName, competitor_niche: compNiche, our_brand: compOurBrand,
            }))} loading={compApi.loading}>🔎 Run Competitor Audit</Btn>
          </Card>
          <ResultBox data={compApi.data ? { audit: compApi.data.audit } : null} loading={compApi.loading} error={compApi.error} title="Competitor Audit Report" />
        </TwoCol>
      )}

      {/* ── AD COPY GENERATOR ── */}
      {tab === 'adcopy' && (
        <TwoCol>
          <Card>
            <SectionHead title="Ad Copy Generator" sub="Meta · Google · LinkedIn · YouTube — 3 headlines, 2 descriptions, A/B variant" />
            <Select label="Ad Platform" value={adPlatform} onChange={setAdPlatform} options={AD_PLATFORMS} />
            <Select label="Campaign Goal" value={adGoal}  onChange={setAdGoal}     options={AD_GOALS} />
            <Input label="Product / Service"     value={adProduct}  onChange={setAdProduct}  placeholder="e.g. AI-powered CRM for Indian SMBs" />
            <Input label="Target Audience"       value={adAudience} onChange={setAdAudience} placeholder="e.g. Sales managers at B2B companies in India" />
            <Input label="Unique Selling Point"  value={adUSP}      onChange={setAdUSP}      placeholder="e.g. Only CRM with GST integration + Hindi support" />
            <Input label="Monthly Budget (optional)" value={adBudget} onChange={setAdBudget} placeholder="e.g. ₹50,000/month" />
            <Btn onClick={() => adApi.call(() => socialPro('ad_copy', {
              product: adProduct, audience: adAudience, goal: adGoal,
              ad_platform: adPlatform, usp: adUSP, budget_range: adBudget,
            }))} loading={adApi.loading}>📣 Generate Ad Copy</Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="What you get" />
              {['3 headline variations (platform char limits)', '2 description variations', 'Recommended CTA', 'A/B test hook variant', 'Audience targeting suggestions', 'CTR benchmark estimate'].map(i => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: '1px solid #1e2535' }}>
                  <span style={{ color: '#22c55e', fontSize: 12 }}>✓</span>
                  <span style={{ color: '#9ca3af', fontSize: 12 }}>{i}</span>
                </div>
              ))}
            </Card>
            <ResultBox data={adApi.data ? { copy: adApi.data.copy } : null} loading={adApi.loading} error={adApi.error} title="Ad Copy" />
          </div>
        </TwoCol>
      )}

      {/* ── INFLUENCER BRIEF ── */}
      {tab === 'influencer' && (
        <TwoCol>
          <Card>
            <SectionHead title="Influencer Campaign Brief" sub="Full brief with deliverables, dos/don'ts, KPIs, and payment terms" />
            <Input label="Brand Name"          value={infBrand}        onChange={setInfBrand}        placeholder="Your brand" />
            <Input label="Product / Service"   value={infProduct}      onChange={setInfProduct}      placeholder="What are you promoting?" />
            <Input label="Campaign Goal"       value={infGoal}         onChange={setInfGoal}         placeholder="e.g. Drive app installs, brand awareness in Tier 2 cities" />
            <Input label="Influencer Niche"    value={infNiche}        onChange={setInfNiche}        placeholder="e.g. Tech YouTubers, Finance Instagram creators, Mom bloggers" />
            <Input label="Deliverables Required" value={infDeliverables} onChange={setInfDeliverables} placeholder="e.g. 2 Reels, 3 Stories, 1 YouTube integration" />
            <Input label="Budget per Influencer" value={infBudget}     onChange={setInfBudget}      />
            <Input label="Campaign Timeline"   value={infTimeline}     onChange={setInfTimeline}    />
            <Input label="Brand Dos / Don'ts"  value={infDosDonts}     onChange={setInfDosDonts}     rows={2} placeholder="e.g. Don't mention competitor X. Must show product in use." />
            <Btn onClick={() => infApi.call(() => socialPro('influencer_brief', {
              brand_name: infBrand, product: infProduct, campaign_goal: infGoal,
              influencer_niche: infNiche, deliverables: infDeliverables,
              budget: infBudget, timeline: infTimeline, dos_donts: infDosDonts,
            }))} loading={infApi.loading}>🤝 Generate Influencer Brief</Btn>
          </Card>
          <ResultBox data={infApi.data ? { brief: infApi.data.brief } : null} loading={infApi.loading} error={infApi.error} title="Influencer Campaign Brief" />
        </TwoCol>
      )}

      {/* ── CRISIS RESPONSE ── */}
      {tab === 'crisis' && (
        <TwoCol>
          <Card>
            <SectionHead title="Brand Crisis Response Handler" sub="Calm, legally safe response drafts for any severity level" />
            <div style={{ padding: 10, background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#f87171' }}>🚨 Act fast. A brand crisis handled in the first hour is 3x more likely to be contained.</div>
            </div>
            <Input  label="Brand Name"     value={crisBrand}    onChange={setCrisBrand}    placeholder="Your brand name" />
            <Select label="Crisis Type"    value={crisType}     onChange={setCrisType}     options={CRISIS_TYPES} />
            <Select label="Severity Level" value={crisSeverity} onChange={setCrisSeverity} options={SEVERITY} />
            <Input  label="Crisis Details" value={crisDetail}   onChange={setCrisDetail}   rows={4}
              placeholder="Describe what happened — what was posted, where, how many saw it, what's the core complaint..." />
            <Btn onClick={() => crisApi.call(() => socialPro('crisis_response', {
              brand_name: crisBrand, crisis_type: crisType,
              crisis_detail: crisDetail, severity: crisSeverity,
            }))} loading={crisApi.loading}>🚨 Generate Crisis Response</Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Response Package Includes" />
              {['Immediate holding statement (post within 1 hour)', 'Full public response for social', 'Direct reply to complainant', 'Internal team communication', 'Follow-up post (24-48hr resolution)', 'What NOT to say (legal red flags)', 'Sentiment monitoring keywords', 'Escalation recommendation'].map(i => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: '1px solid #1e2535' }}>
                  <span style={{ color: '#f87171', fontSize: 12 }}>→</span>
                  <span style={{ color: '#9ca3af', fontSize: 12 }}>{i}</span>
                </div>
              ))}
            </Card>
            <ResultBox data={crisApi.data ? { response: crisApi.data.response } : null} loading={crisApi.loading} error={crisApi.error} title="Crisis Response Package" />
          </div>
        </TwoCol>
      )}

      {/* ── YOUTUBE SCRIPT ── */}
      {tab === 'youtube' && (
        <TwoCol>
          <Card>
            <SectionHead title="YouTube Script Writer" sub="Hook → chapters → B-roll notes → CTA → SEO package" />
            <Input  label="Video Topic"      value={ytTopic}    onChange={setYtTopic}    placeholder="e.g. How to file GST returns in 2026 — complete guide" />
            <Input  label="Channel Niche"    value={ytNiche}    onChange={setYtNiche}    placeholder="e.g. Finance for Indian SMBs" />
            <Select label="Video Style"      value={ytStyle}    onChange={setYtStyle}    options={YT_STYLES} />
            <Input  label="Brand / Channel"  value={ytBrand}    onChange={setYtBrand}    placeholder="Your channel name" />
            <Input  label="CTA Goal"         value={ytCta}      onChange={setYtCta}      placeholder="e.g. Subscribe, download free template, book a call" />
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 11, color: '#6b7280', display: 'block', marginBottom: 6 }}>Target Duration: {ytDuration} minutes</label>
              <input type="range" min={3} max={20} value={ytDuration} onChange={e => setYtDuration(+e.target.value)}
                style={{ width: '100%', accentColor: '#3b82f6' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#6b7280' }}>
                <span>3 min</span><span>20 min</span>
              </div>
            </div>
            <Btn onClick={() => ytApi.call(() => socialPro('youtube_script', {
              topic: ytTopic, channel_niche: ytNiche, duration_min: ytDuration,
              style: ytStyle, brand_name: ytBrand, cta: ytCta,
            }))} loading={ytApi.loading}>▶️ Write YouTube Script</Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Script Includes" />
              {['HOOK (0–30s) — scroll-stopping opening', 'INTRO — who you are + what they learn', 'Chapter breakdown with timestamps', 'Full script for each chapter', 'B-roll visual suggestions', 'Mid-roll + end-screen CTA', '3 title options + meta description', '15 SEO tags + thumbnail text'].map(i => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: '1px solid #1e2535' }}>
                  <span style={{ color: '#f59e0b', fontSize: 12 }}>▶</span>
                  <span style={{ color: '#9ca3af', fontSize: 12 }}>{i}</span>
                </div>
              ))}
            </Card>
            <ResultBox data={ytApi.data ? { script: ytApi.data.script } : null} loading={ytApi.loading} error={ytApi.error} title="YouTube Script" />
          </div>
        </TwoCol>
      )}

      {/* ── EMAIL SEQUENCE ── */}
      {tab === 'email' && (
        <TwoCol>
          <Card>
            <SectionHead title="Email Campaign Sequence" sub="Multi-email sequences with subject lines, body, CTA, and timing" />
            <Select label="Sequence Type" value={emailType}   onChange={setEmailType}    options={SEQ_TYPES} />
            <Select label="Tone"          value={emailTone}   onChange={setEmailTone}    options={TONES} />
            <Input  label="Product / Service"  value={emailProduct}   onChange={setEmailProduct}  placeholder="What are you selling / onboarding for?" />
            <Input  label="Target Audience"    value={emailAudience}  onChange={setEmailAudience} placeholder="e.g. New users who signed up for a free trial" />
            <Input  label="Brand Name"         value={emailBrand}     onChange={setEmailBrand}    placeholder="Your brand" />
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 11, color: '#6b7280', display: 'block', marginBottom: 6 }}>Number of Emails: {emailCount}</label>
              <input type="range" min={3} max={10} value={emailCount} onChange={e => setEmailCount(+e.target.value)}
                style={{ width: '100%', accentColor: '#3b82f6' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#6b7280' }}>
                <span>3 emails</span><span>10 emails</span>
              </div>
            </div>
            <Btn onClick={() => emailApi.call(() => socialPro('email_sequence', {
              sequence_type: emailType, product: emailProduct, audience: emailAudience,
              num_emails: emailCount, brand_name: emailBrand, tone: emailTone,
            }))} loading={emailApi.loading}>📧 Generate Email Sequence</Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Each email includes" />
              {['Send timing (Day 1, Day 3, Day 7...)', 'Subject line — A and B variant', 'Preview text (90 chars)', 'Full email body copy', 'Primary CTA + button text', 'Personalization tokens', 'Goal of this email in sequence'].map(i => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: '1px solid #1e2535' }}>
                  <span style={{ color: '#22c55e', fontSize: 12 }}>✓</span>
                  <span style={{ color: '#9ca3af', fontSize: 12 }}>{i}</span>
                </div>
              ))}
            </Card>
            <ResultBox data={emailApi.data ? { sequence: emailApi.data.sequence } : null} loading={emailApi.loading} error={emailApi.error} title={`${emailCount}-Email Sequence`} />
          </div>
        </TwoCol>
      )}

      {/* ── REEL SCRIPT ── */}
      {tab === 'reel' && (
        <TwoCol>
          <Card>
            <SectionHead title="Reel / Short Video Script" sub="Stop-the-scroll scripts with visual direction, text overlays, and music vibe" />
            <Select label="Platform"    value={reelPlatform} onChange={setReelPlatform} options={[
              { label: 'Instagram Reels', value: 'instagram' },
              { label: 'YouTube Shorts', value: 'youtube_shorts' },
              { label: 'TikTok', value: 'tiktok' },
            ]} />
            <Select label="Hook Style"  value={reelHook}     onChange={setReelHook}     options={HOOK_STYLES} />
            <Select label="Duration"    value={String(reelDuration)} onChange={v => setReelDuration(+v)} options={REEL_DURS.map(d => ({ label: d.label, value: String(d.value) }))} />
            <Input  label="Topic"       value={reelTopic}    onChange={setReelTopic}    placeholder="e.g. 3 GST mistakes that cost Indian businesses lakhs" />
            <Input  label="Brand / Creator Name" value={reelBrand} onChange={setReelBrand} />
            <Btn onClick={() => reelApi.call(() => socialPro('reel_script', {
              topic: reelTopic, duration: reelDuration,
              reel_platform: reelPlatform, hook_style: reelHook, brand_name: reelBrand,
            }))} loading={reelApi.loading}>🎬 Write Reel Script</Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Script Includes" />
              {['Second-by-second breakdown', 'On-screen text overlays', 'Spoken script (conversational)', 'Music / sound vibe recommendation', 'Transition style notes', 'Caption copy + hashtags', '3 thumbnail/cover frame options'].map(i => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: '1px solid #1e2535' }}>
                  <span style={{ color: '#a78bfa', fontSize: 12 }}>🎬</span>
                  <span style={{ color: '#9ca3af', fontSize: 12 }}>{i}</span>
                </div>
              ))}
            </Card>
            <ResultBox data={reelApi.data ? { script: reelApi.data.script } : null} loading={reelApi.loading} error={reelApi.error} title="Reel Script" />
          </div>
        </TwoCol>
      )}

      {/* ── MONTHLY REPORT ── */}
      {tab === 'report' && (
        <TwoCol>
          <Card>
            <SectionHead title="Monthly Performance Report" sub="Raw numbers → written narrative with insights + next month plan" />
            <Input label="Brand Name"      value={repBrandName}   onChange={setRepBrandName}   placeholder="Your brand" />
            <Input label="Month"           value={repMonth}       onChange={setRepMonth}       placeholder="e.g. June 2026" />
            <Input label="Goals Set This Month" value={repGoals}  onChange={setRepGoals}       placeholder="e.g. Reach 10K LinkedIn followers, 5% engagement rate" rows={2} />
            <div style={{ padding: 12, background: '#0f1117', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 8 }}>📊 Enter your platform metrics</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <Input label="Total Followers" value={repFollowers}   onChange={setRepFollowers}   placeholder="e.g. 12,450" />
                <Input label="Posts Published" value={repPosts}       onChange={setRepPosts}       placeholder="e.g. 24" />
                <Input label="Total Reach"     value={repReach}       onChange={setRepReach}       placeholder="e.g. 1,85,000" />
                <Input label="Avg Engagement %" value={repEngagement} onChange={setRepEngagement}  placeholder="e.g. 4.2%" />
              </div>
            </div>
            <Btn onClick={() => reportApi.call(() => socialPro('monthly_report', {
              brand_name: repBrandName, month: repMonth, goals: repGoals,
              metrics: { overall: { followers: repFollowers, posts: repPosts, reach: repReach, engagement_rate: repEngagement } },
            }))} loading={reportApi.loading}>📊 Generate Monthly Report</Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Report Sections" />
              {['Executive summary (3 bullets)', 'Platform-by-platform narrative', 'Top content analysis — why it worked', 'Audience growth quality analysis', 'Engagement rate interpretation', 'Goals vs actuals hit/miss', '3 key learnings', '5 next-month recommendations', 'Suggested targets for next month'].map(i => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: '1px solid #1e2535' }}>
                  <span style={{ color: '#06b6d4', fontSize: 12 }}>📊</span>
                  <span style={{ color: '#9ca3af', fontSize: 12 }}>{i}</span>
                </div>
              ))}
            </Card>
            <ResultBox data={reportApi.data ? { report: reportApi.data.report } : null} loading={reportApi.loading} error={reportApi.error} title="Monthly Report" />
          </div>
        </TwoCol>
      )}

      {/* ── SEO KEYWORD CLUSTER ── */}
      {tab === 'kwcluster' && (
        <TwoCol>
          <Card>
            <SectionHead title="SEO Keyword Cluster Builder" sub="Pillar page + 8 cluster articles + intent map + content calendar" />
            <Input label="Main Topic / Pillar"  value={kwTopic}    onChange={setKwTopic}    placeholder="e.g. GST filing for small businesses India" />
            <Input label="Industry"             value={kwIndustry} onChange={setKwIndustry} placeholder="e.g. Accounting software / Fintech" />
            <Input label="Target Audience"      value={kwAudience} onChange={setKwAudience} placeholder="e.g. Small business owners and CAs in India" />
            <Input label="Market"               value={kwMarket}   onChange={setKwMarket}   placeholder="e.g. India, Global, Tamil Nadu" />
            <div style={{ padding: 10, background: 'rgba(16,185,129,0.07)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#5eead4', marginBottom: 4 }}>🔍 Cluster output</div>
              {['1 pillar page outline (full H2 structure)', '8 cluster article briefs', 'Primary + secondary keywords per article', 'Search intent mapping (TOFU/MOFU/BOFU)', 'Estimated search volume (low/med/high)', 'Internal linking strategy', 'Publish order for max SEO impact', 'Featured snippet opportunities'].map(f => (
                <div key={f} style={{ display: 'flex', gap: 6, padding: '2px 0' }}>
                  <span style={{ color: '#22c55e', fontSize: 11 }}>✓</span>
                  <span style={{ color: '#6b7280', fontSize: 11 }}>{f}</span>
                </div>
              ))}
            </div>
            <Btn onClick={() => kwApi.call(() => socialPro('keyword_cluster', {
              main_topic: kwTopic, industry: kwIndustry, audience: kwAudience, market: kwMarket,
            }))} loading={kwApi.loading}>🔍 Build Keyword Cluster</Btn>
          </Card>
          <ResultBox data={kwApi.data ? { cluster: kwApi.data.cluster } : null} loading={kwApi.loading} error={kwApi.error} title="SEO Keyword Cluster" />
        </TwoCol>
      )}

      {/* ── SEO AUDIT ── */}
      {tab === 'seo' && (
        <TwoCol>
          <Card>
            <SectionHead title="SEO Audit" sub="Technical SEO, on-page analysis, keyword gaps, and 30-60-90 day roadmap" />
            <Input label="Page URL"              value={seoUrl}         onChange={setSeoUrl} />
            <Input label="Target Keywords"       value={seoKeywords}    onChange={setSeoKeywords} rows={2} />
            <Input label="Competitor Sites"      value={seoCompetitors} onChange={setSeoCompetitors} />
            <Input label="Page Content (optional)" value={seoContent}   onChange={setSeoContent} rows={5} placeholder="Paste page content or meta description..." />
            <Btn onClick={() => seoApi.call(() => socialEnhance('seo_audit', {
              url: seoUrl, target_keywords: seoKeywords, competitors: seoCompetitors, page_content: seoContent,
            }))} loading={seoApi.loading}>📈 Run SEO Audit</Btn>
          </Card>
          <ResultBox data={seoApi.data ? { audit: (seoApi.data as any).result } : null} loading={seoApi.loading} error={seoApi.error} title="SEO Audit Report" />
        </TwoCol>
      )}

      {/* ── CAMPAIGN BRIEF ── */}
      {tab === 'campaign' && (
        <TwoCol>
          <Card>
            <SectionHead title="Marketing Campaign Brief" sub="Full campaign strategy with personas, channel mix, KPIs, and content calendar" />
            <Input label="Product / Service"  value={campProduct}  onChange={setCampProduct} />
            <Input label="Target Audience"    value={campAudience} onChange={setCampAudience} rows={2} />
            <Input label="Budget"             value={campBudget}   onChange={setCampBudget} />
            <Input label="Timeline"           value={campTimeline} onChange={setCampTimeline} />
            <Input label="Channels"           value={campChannels} onChange={setCampChannels} />
            <Input label="Primary Goal / KPI" value={campGoal}     onChange={setCampGoal} rows={2} />
            <Btn onClick={() => campaignApi.call(() => socialEnhance('campaign_brief', {
              product: campProduct, target_audience: campAudience, budget: campBudget,
              timeline: campTimeline, channels: campChannels, goal: campGoal,
            }))} loading={campaignApi.loading}>📋 Generate Campaign Brief</Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Brief Includes" />
              {['Campaign theme + tagline', '3 audience personas', 'Messaging hierarchy', 'Channel budget allocation %', '4-week content calendar', 'KPIs + targets', 'A/B test plan', 'Creative brief summary'].map(i => (
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
      {/* ── BRAND KIT ── */}
      {tab === 'brandkit' && (
        <TwoCol>
          <Card>
            <SectionHead title="Brand Kit & Content Pillars" sub="Define your brand once — auto-applied to every post generator" />
            <div style={{ padding: 10, background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#a5b4fc' }}>💾 Saved locally — auto-fills all other tabs</div>
            </div>
            <Input label="Brand Name"       value={bkBrand}    onChange={setBkBrand}    placeholder="e.g. TechFlow Solutions" />
            <Input label="Industry / Niche" value={bkIndustry} onChange={setBkIndustry} placeholder="e.g. B2B SaaS, CA firm, E-commerce" />
            <Input label="Target Audience"  value={bkAudience} onChange={setBkAudience} placeholder="e.g. SMB owners, CTOs, Finance managers" />
            <Select label="Brand Tone"      value={bkTone}     onChange={setBkTone}     options={TONES} />
            <Input label="Your Content Pillars (optional, comma separated)" value={bkPillars} onChange={setBkPillars}
              placeholder="e.g. Education, Product Tips, Customer Stories, Industry News" rows={2} />
            <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
              <Btn onClick={() => {
                localStorage.setItem('social_brand_kit', JSON.stringify({ brand: bkBrand, industry: bkIndustry, audience: bkAudience, tone: bkTone, pillars: bkPillars }))
                alert('Brand Kit saved! ✅ Now auto-fills all tabs.')
              }}>💾 Save Brand Kit</Btn>
              <Btn onClick={() => {
                const saved = localStorage.getItem('social_brand_kit')
                if (saved) {
                  const k = JSON.parse(saved)
                  setBkBrand(k.brand || ''); setBkIndustry(k.industry || '')
                  setBkAudience(k.audience || ''); setBkTone(k.tone || 'professional')
                  setBkPillars(k.pillars || '')
                }
              }}>📂 Load Saved Kit</Btn>
            </div>
            <Btn onClick={() => bkApi.call(() => socialPro('content_pillars', {
              brand_name: bkBrand, industry: bkIndustry, audience: bkAudience,
              pillars: bkPillars ? bkPillars.split(',').map(p => p.trim()) : undefined,
            }))} loading={bkApi.loading}>🏛️ Build Content Pillar Plan</Btn>
          </Card>
          <div>
            {!bkApi.data && (
              <Card>
                <SectionHead title="Content Pillar Plan Includes" />
                {['5 recommended pillars with % allocation', 'Post type mix per pillar (edu/promo/engage)', '10 topic ideas per pillar (50 total)', 'Monthly balance check for 30 posts', 'Sample week calendar with pillar rotation', 'India-specific seasonal pillar', 'Pillar health signals & KPIs'].map(i => (
                  <div key={i} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: '1px solid #1e2535' }}>
                    <span style={{ color: '#818cf8', fontSize: 12 }}>🏛️</span>
                    <span style={{ color: '#9ca3af', fontSize: 12 }}>{i}</span>
                  </div>
                ))}
              </Card>
            )}
            <ResultBox data={bkApi.data ? { plan: bkApi.data.plan } : null} loading={bkApi.loading} error={bkApi.error} title="Content Pillar Strategy" />
          </div>
        </TwoCol>
      )}

      {/* ── BULK GENERATOR ── */}
      {tab === 'bulk' && (
        <TwoCol>
          <Card>
            <SectionHead title="Bulk Post Generator" sub="Generate a week or month of posts in one click" />
            <Select label="Platform"   value={bulkPlatform} onChange={setBulkPlatform} options={PLATFORMS} />
            <Select label="Tone"       value={bulkTone}     onChange={setBulkTone}     options={TONES} />
            <Input  label="Brand Name" value={bulkBrand}    onChange={setBulkBrand}    placeholder="Your brand (optional)" />
            <Input label="Topics (one per line)" value={bulkTopics} onChange={setBulkTopics} rows={10}
              placeholder="Enter one topic per line..." />
            <div style={{ padding: 8, background: 'rgba(16,185,129,0.07)', borderRadius: 6, marginBottom: 12, fontSize: 11, color: '#5eead4' }}>
              {bulkTopics.split('\n').filter(t => t.trim()).length} posts will be generated
            </div>
            <Btn onClick={() => bulkApi.call(() => socialPro('bulk_generate', {
              topics: bulkTopics.split('\n').filter(t => t.trim()),
              tone: bulkTone, brand_name: bulkBrand,
            }, bulkPlatform))} loading={bulkApi.loading}>⚡ Generate All Posts</Btn>
          </Card>
          <div>
            {bulkApi.data?.posts && !bulkApi.loading && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {bulkApi.data.posts.map((p: any, i: number) => (
                  <Card key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Badge text={`Post ${i + 1}`} color="blue" />
                      <Badge text={p.topic?.slice(0, 30) || 'Post'} color="purple" />
                    </div>
                    {p.post_text && (
                      <div style={{ color: '#e2e8f0', fontSize: 12, lineHeight: 1.6, whiteSpace: 'pre-wrap', background: '#0f1117', padding: 10, borderRadius: 6 }}>
                        {p.post_text}
                      </div>
                    )}
                    {p.error && <div style={{ color: '#f87171', fontSize: 11 }}>{p.error}</div>}
                  </Card>
                ))}
              </div>
            )}
            {!bulkApi.data && <ResultBox data={null} loading={bulkApi.loading} error={bulkApi.error} title="Bulk Posts" />}
          </div>
        </TwoCol>
      )}

      {/* ── ANALYTICS ── */}
      {tab === 'analytics' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 16 }}>
            {/* Best Time */}
            <Card>
              <SectionHead title="⏰ Best Time to Post" sub="Optimal schedule for Indian audience" />
              <Select label="Platform" value={anlPlatform} onChange={setAnlPlatform} options={PLATFORMS} />
              <Input  label="Industry" value={anlIndustry} onChange={setAnlIndustry} placeholder="e.g. SaaS, Retail" />
              <Input  label="Audience" value={anlAudience} onChange={setAnlAudience} placeholder="e.g. SMB owners" />
              <Btn onClick={() => timeApi.call(() => socialPro('best_post_time', {
                industry: anlIndustry, audience: anlAudience, timezone: 'IST',
              }, anlPlatform))} loading={timeApi.loading}>⏰ Get Best Times</Btn>
              <ResultBox data={timeApi.data ? { schedule: timeApi.data.schedule } : null} loading={timeApi.loading} error={timeApi.error} title="Optimal Schedule" />
            </Card>

            {/* Engagement Benchmark */}
            <Card>
              <SectionHead title="📊 Engagement Benchmark" sub="Is your rate good or bad for your industry?" />
              <Select label="Platform" value={anlPlatform} onChange={setAnlPlatform} options={PLATFORMS} />
              <Input  label="Industry" value={anlIndustry} onChange={setAnlIndustry} placeholder="e.g. B2B SaaS" />
              <Input  label="Your Engagement Rate %" value={anlRate} onChange={setAnlRate} placeholder="e.g. 3.5" />
              <Input  label="Follower Count" value={anlFollowers} onChange={setAnlFollowers} placeholder="e.g. 12000" />
              <Btn onClick={() => benchApi.call(() => socialPro('benchmark_engagement', {
                industry: anlIndustry, your_rate: parseFloat(anlRate) || 0,
                followers: parseInt(anlFollowers) || 0,
              }, anlPlatform))} loading={benchApi.loading}>📊 Benchmark My Rate</Btn>
              <ResultBox data={benchApi.data ? { analysis: benchApi.data.analysis } : null} loading={benchApi.loading} error={benchApi.error} title="Benchmark Analysis" />
            </Card>

            {/* Performance Score */}
            <Card>
              <SectionHead title="🎯 Content Score" sub="Predict engagement before you post" />
              <Select label="Platform" value={anlPlatform} onChange={setAnlPlatform} options={PLATFORMS} />
              <Input  label="Industry" value={anlIndustry} onChange={setAnlIndustry} placeholder="e.g. Healthcare" />
              <Input  label="Paste your draft post here" value={anlPostText} onChange={setAnlPostText} rows={5}
                placeholder="Paste the post text you want to score..." />
              <Btn onClick={() => scoreApi.call(() => socialPro('performance_score', {
                post_text: anlPostText, industry: anlIndustry, audience: anlAudience,
              }, anlPlatform))} loading={scoreApi.loading}>🎯 Score My Post</Btn>
              <ResultBox data={scoreApi.data ? { analysis: scoreApi.data.analysis } : null} loading={scoreApi.loading} error={scoreApi.error} title="Performance Score" />
            </Card>
          </div>
        </div>
      )}

      {/* ── INDIA & WHATSAPP ── */}
      {tab === 'india' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Row 1: Trending + Regional + WhatsApp */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
            <Card>
              <SectionHead title="India Trending Topics" sub="Festival, news, events — content ideas" />
              <Input label="Your Industry" value={indIndustry} onChange={setIndIndustry} placeholder="e.g. Fintech, FMCG, EdTech" />
              <div style={{ padding: 8, background: 'rgba(255,153,0,0.08)', borderRadius: 6, marginBottom: 12, fontSize: 11, color: '#fbbf24' }}>
                Covers festivals, cricket, Budget, IPL, Republic Day, startup events, seasonal India trends
              </div>
              <Btn onClick={() => trendApi.call(() => socialPro('india_trends', { industry: indIndustry }))} loading={trendApi.loading}>
                Get India Trends
              </Btn>
              <ResultBox data={trendApi.data ? { trends: trendApi.data.trends } : null} loading={trendApi.loading} error={trendApi.error} title="India Content Opportunities" />
            </Card>

            <Card>
              <SectionHead title="Regional Language Post" sub="Tamil, Hindi, Telugu — authentic, not translated" />
              <Select label="Language"   value={indRegLang}  onChange={setIndRegLang}  options={REGIONAL_LANGS} />
              <Select label="Platform"   value={anlPlatform} onChange={setAnlPlatform} options={PLATFORMS} />
              <Input  label="Topic"      value={indRegTopic} onChange={setIndRegTopic} placeholder="e.g. GST filing tips for SMBs" />
              <Input  label="Brand Name" value={indRegBrand} onChange={setIndRegBrand} placeholder="Your brand" />
              <Btn onClick={() => regionalApi.call(() => socialPro('regional_post', {
                topic: indRegTopic, regional_language: indRegLang, brand_name: indRegBrand,
              }, anlPlatform))} loading={regionalApi.loading}>Generate Regional Post</Btn>
              <ResultBox data={regionalApi.data ? { post: regionalApi.data.post } : null} loading={regionalApi.loading} error={regionalApi.error} title="Regional Post" />
            </Card>

            <Card>
              <SectionHead title="WhatsApp Business Content" sub="Broadcast, Catalogue, Abandoned Cart, Reviews" />
              <Select label="Message Type"   value={waType}      onChange={setWaType}      options={WA_TYPES} />
              <Input  label="Brand Name"     value={waBrand}     onChange={setWaBrand}     placeholder="Your business name" />
              <Input  label="Industry"       value={waIndustry}  onChange={setWaIndustry}  placeholder="e.g. Apparel, Restaurant" />
              <Input  label="Product / Service" value={waProduct} onChange={setWaProduct}  placeholder="e.g. Summer Collection" />
              <Input  label="Offer / Context"   value={waOffer}  onChange={setWaOffer}     placeholder="e.g. 20% off this weekend" />
              <div style={{ padding: 8, background: 'rgba(37,211,102,0.08)', borderRadius: 6, marginBottom: 12, fontSize: 11, color: '#4ade80' }}>
                Gets: Primary message + Alternate version + Quick reply buttons + Follow-up + Best send time + Open rate benchmark
              </div>
              <Btn onClick={() => waApi.call(() => socialAction('whatsapp_content', {
                content_type: waType, brand_name: waBrand, industry: waIndustry,
                product_name: waProduct, offer: waOffer,
              }))} loading={waApi.loading}>Generate WhatsApp Content</Btn>
              <ResultBox data={waApi.data} loading={waApi.loading} error={waApi.error} title="WhatsApp Messages" />
            </Card>
          </div>

          {/* Row 2: Indian Cultural Calendar — KILLER DIFFERENTIATOR */}
          <Card>
            <SectionHead
              title="Indian Cultural Calendar — Festival Campaign Planner"
              sub="Diwali, Pongal, Holi, Eid, Republic Day — ready-to-post campaign briefs. Zero competitors offer this."
            />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 12, marginBottom: 16 }}>
              <Input  label="Brand Name"  value={calBrandName}   onChange={setCalBrandName}   placeholder="e.g. Raju Textiles" />
              <Input  label="Industry"    value={calIndustryCC}  onChange={setCalIndustryCC}  placeholder="e.g. Apparel, Fintech" />
              <Select label="Tone"        value={calTone}        onChange={setCalTone}         options={CAL_TONES} />
              <Select label="Language"    value={calLang}        onChange={setCalLang}         options={LANG_OPTIONS} />
            </div>
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 8, fontWeight: 600 }}>SELECT MONTHS</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {MONTHS.map(m => (
                  <button key={m} onClick={() => toggleMonth(m)} style={{
                    padding: '4px 12px', borderRadius: 20, fontSize: 11, cursor: 'pointer', border: 'none',
                    background: calSelectedMonths.includes(m) ? 'rgba(16,185,129,0.2)' : '#1e2535',
                    color: calSelectedMonths.includes(m) ? '#10b981' : '#6b7280',
                    fontWeight: calSelectedMonths.includes(m) ? 600 : 400,
                  }}>{m}</button>
                ))}
              </div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 8, fontWeight: 600 }}>SELECT PLATFORMS</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {CAL_PLATFORMS.map(p => (
                  <button key={p} onClick={() => togglePlatform(p)} style={{
                    padding: '4px 12px', borderRadius: 20, fontSize: 11, cursor: 'pointer', border: 'none', textTransform: 'capitalize',
                    background: calPlatforms.includes(p) ? 'rgba(99,102,241,0.2)' : '#1e2535',
                    color: calPlatforms.includes(p) ? '#a5b4fc' : '#6b7280',
                    fontWeight: calPlatforms.includes(p) ? 600 : 400,
                  }}>{p}</button>
                ))}
              </div>
            </div>
            <Btn
              onClick={() => culturalApi.call(() => socialAction('cultural_calendar', {
                brand_name: calBrandName, industry: calIndustryCC,
                months: calSelectedMonths, platforms: calPlatforms, tone: calTone,
              }, 'all', calLang))}
              loading={culturalApi.loading}
              disabled={calSelectedMonths.length === 0 || !calBrandName}
            >
              Generate Festival Campaigns
            </Btn>
            {culturalApi.data?.campaigns?.length > 0 && (
              <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
                {culturalApi.data.campaigns.map((c: any, i: number) => (
                  <div key={i} style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 10, padding: '14px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                      <span style={{ color: '#f59e0b', fontWeight: 700, fontSize: 14 }}>{c.event}</span>
                      <span style={{ fontSize: 11, color: '#6b7280' }}>{c.date}</span>
                    </div>
                    {c.angle && <div style={{ color: '#a5b4fc', fontSize: 12, marginBottom: 6 }}>Angle: {c.angle}</div>}
                    {c.caption && <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6, fontStyle: 'italic' }}>"{c.caption}"</div>}
                    {c.hashtags && <div style={{ fontSize: 11, color: '#10b981' }}>{Array.isArray(c.hashtags) ? c.hashtags.join(' ') : c.hashtags}</div>}
                    {c.dos_donts && <div style={{ marginTop: 8, fontSize: 11, color: '#ef4444', borderTop: '1px solid #1e2535', paddingTop: 8 }}>Do/Don't: {c.dos_donts}</div>}
                  </div>
                ))}
              </div>
            )}
            {culturalApi.data && !culturalApi.data.campaigns?.length && (
              <ResultBox data={culturalApi.data} loading={culturalApi.loading} error={culturalApi.error} title="Festival Campaigns" />
            )}
          </Card>
        </div>
      )}

      {/* ── POST PREVIEW (enhancement — shown inside Content tab result area) ── */}
      {tab === 'content' && contentApi.data && !contentApi.loading && (
        <div style={{ marginTop: 16 }}>
          <Card>
            <SectionHead title="🔍 Post Preview & Score" sub="Check your post before publishing" />
            <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', marginBottom: 8 }}>
              <div style={{ flex: 1 }}>
                <Input label="Paste post to preview" value={previewText} onChange={setPreviewText} rows={3}
                  placeholder="Paste the generated post text here to check it..." />
              </div>
              <Select label="Platform" value={previewPlatform} onChange={setPreviewPlatform} options={PLATFORMS} />
            </div>
            <Btn onClick={() => previewApi.call(() => socialPro('post_preview', { post_text: previewText }, previewPlatform))} loading={previewApi.loading}>
              🔍 Check Post
            </Btn>
            {previewApi.data && !previewApi.loading && (() => {
              const d = previewApi.data
              return (
                <div style={{ marginTop: 12 }}>
                  <div style={{ display: 'flex', gap: 12, marginBottom: 10 }}>
                    <div style={{ padding: '8px 16px', borderRadius: 8, background: d.score >= 80 ? 'rgba(34,197,94,0.15)' : d.score >= 50 ? 'rgba(251,191,36,0.15)' : 'rgba(239,68,68,0.15)', border: `1px solid ${d.score >= 80 ? '#22c55e' : d.score >= 50 ? '#fbbf24' : '#ef4444'}` }}>
                      <div style={{ fontSize: 24, fontWeight: 700, color: d.score >= 80 ? '#22c55e' : d.score >= 50 ? '#fbbf24' : '#ef4444' }}>{d.score}/100</div>
                      <div style={{ fontSize: 10, color: '#6b7280' }}>Post Score</div>
                    </div>
                    <div style={{ padding: '8px 16px', borderRadius: 8, background: 'rgba(16,185,129,0.07)' }}>
                      <div style={{ fontSize: 16, fontWeight: 600, color: d.within_limit ? '#22c55e' : '#ef4444' }}>{d.char_count}/{d.max_chars}</div>
                      <div style={{ fontSize: 10, color: '#6b7280' }}>Characters</div>
                    </div>
                    <div style={{ padding: '8px 16px', borderRadius: 8, background: 'rgba(16,185,129,0.07)' }}>
                      <div style={{ fontSize: 16, fontWeight: 600, color: d.hashtag_count <= d.hashtag_limit ? '#22c55e' : '#ef4444' }}>{d.hashtag_count}/{d.hashtag_limit}</div>
                      <div style={{ fontSize: 10, color: '#6b7280' }}>Hashtags</div>
                    </div>
                  </div>
                  {d.issues?.length > 0 && (
                    <div style={{ marginBottom: 8 }}>
                      {d.issues.map((issue: string, i: number) => (
                        <div key={i} style={{ padding: '4px 10px', marginBottom: 4, borderRadius: 6, background: 'rgba(239,68,68,0.1)', color: '#f87171', fontSize: 12 }}>⚠️ {issue}</div>
                      ))}
                    </div>
                  )}
                  {d.tips?.length > 0 && (
                    <div>
                      {d.tips.map((tip: string, i: number) => (
                        <div key={i} style={{ padding: '4px 10px', marginBottom: 4, borderRadius: 6, background: 'rgba(59,130,246,0.1)', color: '#93c5fd', fontSize: 12 }}>💡 {tip}</div>
                      ))}
                    </div>
                  )}
                  {d.issues?.length === 0 && d.tips?.length === 0 && (
                    <div style={{ color: '#22c55e', fontSize: 12 }}>✅ Post looks good! Ready to publish.</div>
                  )}
                  {previewText && (
                    <Btn onClick={() => addToQueue({ topic: previewText.slice(0, 50), platform: previewPlatform, text: previewText })} style={{ marginTop: 8 }}>
                      ➕ Add to Post Queue
                    </Btn>
                  )}
                </div>
              )
            })()}
          </Card>
        </div>
      )}

      {/* ── NICHE TEMPLATES ── */}
      {tab === 'templates' && (
        <TwoCol>
          <Card>
            <SectionHead title="Niche Social Media Templates" sub="Industry-specific ready-to-post template packs for Indian businesses" />
            <Select label="Business Type" value={ntNiche} onChange={setNtNiche} options={NICHES} />
            <Input  label="Brand Name"    value={ntBrand} onChange={setNtBrand} placeholder="Your brand name" />
            <Input  label="Month (optional)" value={ntMonth} onChange={setNtMonth} placeholder="e.g. July 2026 (auto-detects if blank)" />
            <div style={{ padding: 10, background: 'rgba(16,185,129,0.07)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#5eead4', marginBottom: 6 }}>🗂️ Each template pack includes</div>
              {['10 ready-to-copy post templates', 'Educational + Promotional + Seasonal mix', 'Platform recommendation per template', 'Suggested image type', '2 templates in Tamil or Hindi', '2 WhatsApp broadcast variants', 'Month-specific compliance dates / events'].map(f => (
                <div key={f} style={{ display: 'flex', gap: 6, padding: '2px 0' }}>
                  <span style={{ color: '#22c55e', fontSize: 11 }}>✓</span>
                  <span style={{ color: '#6b7280', fontSize: 11 }}>{f}</span>
                </div>
              ))}
            </div>
            <Btn onClick={() => ntApi.call(() => socialPro('niche_templates', {
              niche: ntNiche, brand_name: ntBrand, month: ntMonth,
            }))} loading={ntApi.loading}>🗂️ Generate Template Pack</Btn>
          </Card>
          <ResultBox data={ntApi.data ? { templates: ntApi.data.templates } : null} loading={ntApi.loading} error={ntApi.error} title="Template Pack" />
        </TwoCol>
      )}

      {/* ── CALENDAR & QUEUE ── */}
      {tab === 'calendar' && (
        <TwoCol>
          <Card>
            <SectionHead title="Content Calendar Generator" sub="Plan 7–30 days of posts in one click" />
            <Input  label="Brand Name"   value={calBrand}    onChange={setCalBrand}    placeholder="Your brand" />
            <Input  label="Industry"     value={calIndustry} onChange={setCalIndustry} placeholder="e.g. SaaS, Retail, Healthcare" />
            <Input  label="Platforms (comma separated)" value={calPlats} onChange={setCalPlats} placeholder="linkedin, twitter, instagram" />
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 11, color: '#6b7280', display: 'block', marginBottom: 6 }}>Days: {calDays}</label>
              <input type="range" min={7} max={30} value={calDays} onChange={e => setCalDays(+e.target.value)} style={{ width: '100%', accentColor: '#3b82f6' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#6b7280' }}><span>7 days</span><span>30 days</span></div>
            </div>
            <Btn onClick={() => calApi.call(() => socialPro('calendar', {
              brand_name: calBrand, industry: calIndustry,
              platforms: calPlats.split(',').map(p => p.trim()),
              days: calDays, post_per_day: 1,
            }))} loading={calApi.loading}>📅 Generate Calendar</Btn>

            {calApi.data?.calendar && !calApi.loading && (
              <div style={{ marginTop: 14 }}>
                <SectionHead title="Generated Plan" />
                {calApi.data.calendar.map((day: any, i: number) => (
                  <div key={i} style={{ padding: '8px 10px', marginBottom: 6, borderRadius: 8, background: '#0f1117', border: '1px solid #1e2535' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ color: '#5eead4', fontSize: 12, fontWeight: 600 }}>{day.date || `Day ${day.day}`}</span>
                      <Badge text={day.post_type || 'post'} color="blue" />
                    </div>
                    <div style={{ color: '#e2e8f0', fontSize: 12 }}>{day.topic}</div>
                    {day.brief && <div style={{ color: '#6b7280', fontSize: 11, marginTop: 3 }}>{day.brief}</div>}
                    <div style={{ display: 'flex', gap: 6, marginTop: 6, flexWrap: 'wrap' }}>
                      <Btn onClick={() => addToQueue({ topic: day.topic, platform: calPlats.split(',')[0]?.trim() || 'linkedin', text: day.brief || day.topic })}
                        style={{ padding: '3px 8px', fontSize: 11 }}>
                        ➕ Add to Queue
                      </Btn>
                      <Btn onClick={() => repurposeCalItem(i, day.brief || day.topic)} loading={repurposeLoading[i]}
                        style={{ padding: '3px 8px', fontSize: 11, background: 'rgba(59,130,246,0.15)', borderColor: 'rgba(59,130,246,0.4)' }}>
                        ♻️ Repurpose
                      </Btn>
                    </div>
                    {repurposeResults[i] && (
                      <div style={{ marginTop: 8, padding: 10, background: '#0a0d14', borderRadius: 6, border: '1px solid rgba(59,130,246,0.3)' }}>
                        <div style={{ fontSize: 10, color: '#3b82f6', marginBottom: 4 }}>Repurposed post</div>
                        <div style={{ color: '#e2e8f0', fontSize: 11, whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>{repurposeResults[i]}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>

          <div>
            <Card>
              <SectionHead title="📋 Post Queue" sub={`${queue.length} posts • Draft/Scheduled/Posted tracking`} />
              {queue.length === 0 && (
                <div style={{ color: '#6b7280', fontSize: 12, padding: 16, textAlign: 'center' }}>
                  No posts in queue yet. Generate a calendar and add posts, or use "Add to Queue" from the Content tab.
                </div>
              )}
              {queue.map(post => (
                <div key={post.id} style={{ padding: 10, marginBottom: 8, borderRadius: 8, background: '#0f1117', border: `1px solid ${STATUS_COLORS[post.status]}33` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, alignItems: 'center' }}>
                    <Badge text={post.platform.toUpperCase()} color="blue" />
                    <select value={post.status} onChange={e => updateStatus(post.id, e.target.value as PostStatus)}
                      style={{ background: '#1a1f2e', border: `1px solid ${STATUS_COLORS[post.status]}`, borderRadius: 4, color: STATUS_COLORS[post.status], fontSize: 11, padding: '2px 6px', cursor: 'pointer' }}>
                      {POST_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                  <div style={{ color: '#e2e8f0', fontSize: 12, lineHeight: 1.5, marginBottom: 6 }}>
                    {post.text.length > 120 ? post.text.slice(0, 120) + '...' : post.text}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 6 }}>
                    <span style={{ color: '#4b5563', fontSize: 10 }}>{new Date(post.createdAt).toLocaleDateString()}</span>
                    <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                      <button onClick={() => submitForApproval(post.text, post.platform, post.topic)}
                        style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: 4, color: '#5eead4', cursor: 'pointer', fontSize: 10, padding: '2px 7px' }}>
                        📤 Send for Review
                      </button>
                      <button onClick={() => removeFromQueue(post.id)} style={{ background: 'none', border: 'none', color: '#6b7280', cursor: 'pointer', fontSize: 11 }}>✕</button>
                    </div>
                  </div>
                </div>
              ))}
              {queue.length > 0 && (
                <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
                  {POST_STATUSES.map(s => (
                    <div key={s} style={{ fontSize: 11, color: STATUS_COLORS[s] }}>
                      {s}: {queue.filter(p => p.status === s).length}
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </TwoCol>
      )}

      {/* ── MONITOR ── */}
      {tab === 'monitor' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 16 }}>
            {/* Brand Mention Monitor */}
            <Card>
              <SectionHead title="👁️ Brand Mention Monitor" sub="Sentiment, viral risk, competitor activity" />
              <Input label="Your Brand"     value={monBrand}       onChange={setMonBrand}       placeholder="e.g. TechFlow" />
              <Input label="Industry"       value={monIndustry}    onChange={setMonIndustry}    placeholder="e.g. B2B SaaS" />
              <Input label="Competitors (comma separated)" value={monCompetitors} onChange={setMonCompetitors} placeholder="Zoho, HubSpot, Freshworks" />
              <Btn onClick={() => monitorApi.call(() => socialPro('brand_monitor', {
                brand_name: monBrand, industry: monIndustry,
                competitors: monCompetitors ? monCompetitors.split(',').map(c => c.trim()) : [],
              }))} loading={monitorApi.loading}>👁️ Run Brand Monitor</Btn>
              <ResultBox data={monitorApi.data ? { intelligence: monitorApi.data.intelligence } : null} loading={monitorApi.loading} error={monitorApi.error} title="Brand Intelligence" />
            </Card>

            {/* Competitor Post Tracker */}
            <Card>
              <SectionHead title="🕵️ Competitor Post Tracker" sub="What did they post this week? Counter-strategy" />
              <Input label="Competitor Name" value={ctrCompName} onChange={setCtrCompName} placeholder="e.g. Zoho CRM" />
              <Input label="Their Niche"     value={ctrNiche}    onChange={setCtrNiche}    placeholder="e.g. CRM for Indian SMBs" />
              <Input label="Our Brand"       value={ctrOurBrand} onChange={setCtrOurBrand} placeholder="Your brand name" />
              <Btn onClick={() => ctrApi.call(() => socialPro('competitor_tracker', {
                competitor_name: ctrCompName, niche: ctrNiche, our_brand: ctrOurBrand, timeframe: 'last_week',
              }))} loading={ctrApi.loading}>🕵️ Track This Week</Btn>
              <ResultBox data={ctrApi.data ? { report: ctrApi.data.report } : null} loading={ctrApi.loading} error={ctrApi.error} title="Competitor Report" />
            </Card>

            {/* Unified Analytics */}
            <Card>
              <SectionHead title="📊 Unified Analytics" sub="Cross-platform narrative + next period strategy" />
              <Input label="Brand Name" value={uaBrand} onChange={setUaBrand} placeholder="Your brand" />
              <div style={{ padding: 8, background: '#0f1117', borderRadius: 6, marginBottom: 10 }}>
                <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 6 }}>Enter followers for each platform</div>
                <Input label="LinkedIn followers" value={uaLI} onChange={setUaLI} placeholder="e.g. 5000" />
                <Input label="Twitter followers"  value={uaTW} onChange={setUaTW} placeholder="e.g. 2000" />
                <Input label="Instagram followers" value={uaIG} onChange={setUaIG} placeholder="e.g. 3000" />
              </div>
              <Btn onClick={() => uaApi.call(() => socialPro('unified_analytics', {
                brand_name: uaBrand, period: uaPeriod,
                metrics: {
                  ...(uaLI ? { linkedin: { followers: uaLI } } : {}),
                  ...(uaTW ? { twitter: { followers: uaTW } } : {}),
                  ...(uaIG ? { instagram: { followers: uaIG } } : {}),
                },
              }))} loading={uaApi.loading}>📊 Generate Unified Report</Btn>
              <ResultBox data={uaApi.data ? { report: uaApi.data.report } : null} loading={uaApi.loading} error={uaApi.error} title="Unified Analytics" />
            </Card>
          </div>
        </div>
      )}

      {/* ── CONTENT BRIDGE ── */}
      {tab === 'bridge' && (
        <TwoCol>
          <Card>
            <SectionHead title="Cross-Agent Content Bridge" sub="CRM win / HR hire / Product launch → auto social post" />
            <div style={{ padding: 10, background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#a5b4fc' }}>🔗 Connects your business events to social content — no copy-pasting between tools</div>
            </div>
            <Select label="Event Type"    value={bridgeTrigger}  onChange={setBridgeTrigger}  options={TRIGGER_TYPES} />
            <Select label="Post Platform" value={bridgePlatform} onChange={setBridgePlatform} options={PLATFORMS} />
            <Select label="Tone"          value={bridgeTone}     onChange={setBridgeTone}     options={TONES} />
            <Input  label="Brand Name"    value={bridgeBrand}    onChange={setBridgeBrand}    placeholder="Your brand" />

            {/* Dynamic fields based on trigger type */}
            {bridgeTrigger === 'crm_deal_won' && <>
              <Input label="Client / Company Name" value={bridgeClient} onChange={setBridgeClient} placeholder="e.g. Acme Corp" />
              <Input label="Deal Value"             value={bridgeValue}  onChange={setBridgeValue}  placeholder="e.g. ₹12 lakhs" />
            </>}
            {bridgeTrigger === 'hr_hire' && <>
              <Input label="Role / Designation"  value={bridgeRole} onChange={setBridgeRole} placeholder="e.g. Senior Product Designer" />
              <Input label="Department"          value={bridgeDept} onChange={setBridgeDept} placeholder="e.g. Product, Engineering" />
            </>}
            {bridgeTrigger === 'product_launch' && <>
              <Input label="Product / Feature Name" value={bridgeProduct} onChange={setBridgeProduct} placeholder="e.g. AI Dashboard v2.0" />
            </>}
            {bridgeTrigger === 'milestone' && <>
              <Input label="Milestone Description" value={bridgeMilestone} onChange={setBridgeMilestone} placeholder="e.g. 1000 customers, ₹1 Cr ARR, 5 years" />
            </>}
            {bridgeTrigger === 'event' && <>
              <Input label="Event Name" value={bridgeEventName} onChange={setBridgeEventName} placeholder="e.g. AI for SMBs Webinar" />
            </>}
            {bridgeTrigger === 'award' && <>
              <Input label="Award Name"      value={bridgeAward}  onChange={setBridgeAward}  placeholder="e.g. Best SaaS Startup 2026" />
            </>}
            {bridgeTrigger === 'client_success' && <>
              <Input label="Client Name"  value={bridgeClient}    onChange={setBridgeClient}    placeholder="Client company" />
              <Input label="Result / ROI" value={bridgeResult}    onChange={setBridgeResult}    placeholder="e.g. 40% cost reduction in 3 months" />
            </>}

            <Btn onClick={() => bridgeApi.call(() => socialPro('cross_agent_content', {
              trigger_type: bridgeTrigger,
              brand_name: bridgeBrand,
              tone: bridgeTone,
              event_data: {
                client: bridgeClient, value: bridgeValue, role: bridgeRole,
                department: bridgeDept, product: bridgeProduct, milestone: bridgeMilestone,
                name: bridgeEventName, award: bridgeAward, result: bridgeResult,
              },
            }, bridgePlatform))} loading={bridgeApi.loading}>🔗 Generate Social Post from Event</Btn>
          </Card>

          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Post Includes" />
              {['Primary post (storytelling, not press release)', 'Short version for Twitter/Stories', '3 hook options to A/B test', 'Image/visual suggestion', '5 hashtags', 'Who on team to tag (by role)', '2 repurpose ideas from same event'].map(i => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: '1px solid #1e2535' }}>
                  <span style={{ color: '#818cf8', fontSize: 12 }}>🔗</span>
                  <span style={{ color: '#9ca3af', fontSize: 12 }}>{i}</span>
                </div>
              ))}
            </Card>
            <ResultBox data={bridgeApi.data ? { post: bridgeApi.data.post } : null} loading={bridgeApi.loading} error={bridgeApi.error} title="Generated Social Post" />
          </div>
        </TwoCol>
      )}

      {/* ── AI CONTENT SCHEDULER ── */}
      {tab === 'scheduler' && (
        <TwoCol>
          <Card>
            <SectionHead title="AI Content Scheduler" sub="Generate a full week/month schedule with optimal times & ready captions" />
            <Input label="Brand Name" value={schBrand} onChange={setSchBrand} placeholder="Sri Lakshmi Stores" />
            <Input label="Industry" value={schIndustry} onChange={setSchIndustry} placeholder="e.g. Retail, SaaS, Food, Education" />
            <Input label="Campaign Goal" value={schGoal} onChange={setSchGoal} placeholder="e.g. brand awareness, lead gen, sales" />
            <Input label="Target Audience" value={schAudience} onChange={setSchAudience} placeholder="e.g. small business owners in Tamil Nadu" />
            <Select label="Days to Schedule" value={schDays} onChange={setSchDays} options={[{ label: '7 days', value: '7' }, { label: '14 days', value: '14' }, { label: '30 days', value: '30' }]} />
            <div style={{ marginTop: 14 }}>
              <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 8 }}>Platforms</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {CAL_PLATFORMS.map(p => (
                  <span key={p} onClick={() => toggleSchPlatform(p)} style={{ cursor: 'pointer', padding: '5px 12px', borderRadius: 20, fontSize: 12, fontWeight: 600, textTransform: 'capitalize', background: schPlatforms.includes(p) ? '#818cf8' : '#1e2535', color: schPlatforms.includes(p) ? '#fff' : '#9ca3af', border: schPlatforms.includes(p) ? '1px solid #818cf8' : '1px solid #374151', transition: 'all .15s' }}>{p}</span>
                ))}
              </div>
            </div>
            <Btn onClick={runScheduler} loading={schLoading} style={{ marginTop: 16, width: '100%' }}>Generate Schedule</Btn>
            {schErr && <div style={{ color: '#ef4444', fontSize: 13, marginTop: 8 }}>{schErr}</div>}

            {schRes?.pillar_distribution && (
              <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid #1e2535' }}>
                <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 10 }}>Content Pillar Mix</div>
                {Object.entries(schRes.pillar_distribution).map(([pillar, pct]: any) => (
                  <div key={pillar} style={{ marginBottom: 6 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                      <span style={{ color: '#e2e8f0', fontSize: 12 }}>{pillar}</span>
                      <span style={{ color: '#818cf8', fontSize: 12, fontWeight: 600 }}>{pct}%</span>
                    </div>
                    <div style={{ height: 4, background: '#1e2535', borderRadius: 2 }}>
                      <div style={{ height: '100%', width: `${pct}%`, background: '#818cf8', borderRadius: 2 }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card>
            <SectionHead title="Your Content Schedule" sub={schRes ? `${schRes.days} days · ${schRes.platforms?.join(', ')}` : ''} />
            {schRes?.schedule ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {schRes.summary && <div style={{ color: '#818cf8', fontSize: 13, marginBottom: 10, padding: '8px 12px', background: 'rgba(129,140,248,0.08)', borderRadius: 6 }}>{schRes.summary}</div>}
                {(schRes.schedule as any[]).map((day: any, di: number) => {
                  const open = schExpandDay === di
                  return (
                    <div key={di} style={{ background: '#0f1117', borderRadius: 8, overflow: 'hidden', border: '1px solid #1e2535' }}>
                      <div onClick={() => setSchExpandDay(open ? null : di)} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px' }}>
                        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                          <span style={{ color: '#818cf8', fontWeight: 700, fontSize: 13 }}>Day {day.day}</span>
                          <span style={{ color: '#6b7280', fontSize: 12 }}>{day.date}</span>
                          <span style={{ background: '#1e2535', color: '#a5b4fc', fontSize: 10, padding: '2px 8px', borderRadius: 10, fontWeight: 600 }}>{day.pillar}</span>
                        </div>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <span style={{ color: '#6b7280', fontSize: 11 }}>{day.posts?.length} posts</span>
                          <span style={{ color: '#6b7280', fontSize: 14 }}>{open ? '▲' : '▼'}</span>
                        </div>
                      </div>
                      {open && (
                        <div style={{ padding: '0 14px 14px' }}>
                          {day.topic && <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 10, fontStyle: 'italic' }}>Topic: {day.topic}</div>}
                          {(day.posts || []).map((post: any, pi: number) => (
                            <div key={pi} style={{ background: '#161b27', borderRadius: 8, padding: '10px 12px', marginBottom: 8, border: '1px solid #1e2535' }}>
                              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
                                <Badge label={post.platform} color="#818cf8" />
                                <span style={{ color: '#f59e0b', fontSize: 12, fontWeight: 600 }}>⏰ {post.time}</span>
                                <span style={{ color: '#6b7280', fontSize: 11 }}>{post.time_label}</span>
                              </div>
                              <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.6, marginBottom: 6 }}>{post.caption}</div>
                              {post.hashtags?.length > 0 && (
                                <div style={{ color: '#818cf8', fontSize: 11, marginBottom: 4 }}>{post.hashtags.join(' ')}</div>
                              )}
                              {post.content_tip && (
                                <div style={{ color: '#10b981', fontSize: 11, fontStyle: 'italic' }}>💡 {post.content_tip}</div>
                              )}
                              <div style={{ marginTop: 6 }}>
                                <span onClick={() => navigator.clipboard?.writeText(post.caption)} style={{ cursor: 'pointer', color: '#6b7280', fontSize: 11, padding: '2px 8px', background: '#1e2535', borderRadius: 4 }}>Copy Caption</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            ) : <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>Fill in the form and click Generate Schedule →</div>}
          </Card>
        </TwoCol>
      )}

      {/* ── A/B COPY TESTER ── */}
      {tab === 'abtest' && (
        <TwoCol>
          <Card>
            <SectionHead title="A/B Copy Tester" sub="AI generates multiple hook styles — scored by predicted engagement" />
            <div style={{ marginTop: 10 }}>
              <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Topic / Message</div>
              <textarea value={abTopic} onChange={e => setAbTopic(e.target.value)} rows={3} placeholder="e.g. We just launched home delivery in Chennai — 30 min guaranteed"
                style={{ width: '100%', background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, color: '#e2e8f0', fontSize: 13, padding: '10px 12px', fontFamily: 'inherit', boxSizing: 'border-box', resize: 'vertical' }} />
            </div>
            <Input label="Brand Name" value={abBrand} onChange={setAbBrand} placeholder="Sri Lakshmi Stores" />
            <Input label="Industry" value={abIndustry} onChange={setAbIndustry} placeholder="e.g. Retail, SaaS, Restaurant" />
            <Select label="Platform" value={abPlatform} onChange={setAbPlatform} options={PLATFORMS} />
            <Select label="Goal" value={abGoal} onChange={setAbGoal} options={[
              { label: 'Engagement (comments/shares)', value: 'engagement' },
              { label: 'Lead Generation',              value: 'lead_gen' },
              { label: 'Brand Awareness',              value: 'awareness' },
              { label: 'Sales / Conversions',          value: 'sales' },
            ]} />
            <Select label="Variations" value={abVariations} onChange={setAbVariations} options={[
              { label: '2 variations', value: '2' },
              { label: '3 variations', value: '3' },
              { label: '4 variations', value: '4' },
              { label: '5 variations', value: '5' },
            ]} />
            <Btn onClick={runAbTest} loading={abLoading} disabled={!abTopic} style={{ marginTop: 14, width: '100%' }}>
              Generate A/B Variations
            </Btn>
            {abErr && <div style={{ color: '#ef4444', fontSize: 13, marginTop: 8 }}>{abErr}</div>}

            {abRes?.testing_advice && (
              <div style={{ marginTop: 16, padding: '10px 14px', background: 'rgba(129,140,248,0.07)', border: '1px solid #818cf822', borderRadius: 8 }}>
                <div style={{ color: '#818cf8', fontSize: 11, fontWeight: 700, marginBottom: 4 }}>💡 TESTING ADVICE</div>
                <div style={{ color: '#9ca3af', fontSize: 12, lineHeight: 1.6 }}>{abRes.testing_advice}</div>
              </div>
            )}
          </Card>

          <Card>
            <SectionHead title="Copy Variations" sub={abRes ? `${abRes.variations?.length} variations · Winner highlighted` : ''} />
            {abRes?.variations ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {abRes.winner_reason && (
                  <div style={{ padding: '8px 14px', background: 'rgba(16,185,129,0.08)', border: '1px solid #10b98133', borderRadius: 8, fontSize: 12, color: '#6ee7b7' }}>
                    🏆 {abRes.winner_reason}
                  </div>
                )}
                {(abRes.variations as any[]).map((v: any) => {
                  const isWinner = v.id === abRes.winner_id
                  const isSelected = abSelected === v.id
                  return (
                    <div key={v.id} onClick={() => setAbSelected(isSelected ? null : v.id)} style={{
                      cursor: 'pointer', borderRadius: 10, padding: '14px 16px', transition: 'border .15s',
                      background: isWinner ? 'rgba(16,185,129,0.06)' : '#0f1117',
                      border: isWinner ? '1px solid #10b98155' : isSelected ? '1px solid #818cf888' : '1px solid #1e2535',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <span style={{ background: isWinner ? '#10b981' : '#374151', color: '#fff', fontSize: 11, fontWeight: 700, borderRadius: 4, padding: '2px 8px' }}>
                            {isWinner ? '🏆 Winner' : `#${v.id}`}
                          </span>
                          <span style={{ color: '#818cf8', fontSize: 12, fontWeight: 600 }}>{v.hook_type}</span>
                        </div>
                        <div style={{ display: 'flex', gap: 8 }}>
                          <span style={{ color: '#10b981', fontSize: 12, fontWeight: 700 }}>{v.predicted_engagement}%</span>
                          <span style={{ color: '#6b7280', fontSize: 11 }}>eng.</span>
                        </div>
                      </div>

                      {/* Engagement bar */}
                      <div style={{ height: 3, background: '#1e2535', borderRadius: 2, marginBottom: 10 }}>
                        <div style={{ height: '100%', width: `${v.predicted_engagement}%`, background: isWinner ? '#10b981' : '#818cf8', borderRadius: 2 }} />
                      </div>

                      {/* Hook line */}
                      <div style={{ color: '#f59e0b', fontSize: 13, fontWeight: 600, marginBottom: 6 }}>"{v.hook_line}"</div>

                      {isSelected && (
                        <>
                          <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.7, marginBottom: 10, whiteSpace: 'pre-wrap' }}>{v.full_post}</div>
                          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                            <Badge label={`💬 ${v.predicted_comments} comments`} color="#818cf8" />
                            <Badge label={`↗ ${v.predicted_shares} shares`} color="#06b6d4" />
                            {v.cta && <Badge label={`CTA: ${v.cta.slice(0, 30)}`} color="#6b7280" />}
                          </div>
                          {v.why_it_works && <div style={{ color: '#6b7280', fontSize: 12, fontStyle: 'italic' }}>💡 {v.why_it_works}</div>}
                          <div style={{ marginTop: 8, display: 'flex', gap: 6 }}>
                            <span onClick={e => { e.stopPropagation(); navigator.clipboard?.writeText(v.full_post) }} style={{ cursor: 'pointer', color: '#fff', fontSize: 11, padding: '4px 10px', background: '#374151', borderRadius: 6 }}>Copy Post</span>
                            <span onClick={e => { e.stopPropagation(); navigator.clipboard?.writeText(v.hook_line) }} style={{ cursor: 'pointer', color: '#818cf8', fontSize: 11, padding: '4px 10px', background: '#1e2535', borderRadius: 6 }}>Copy Hook</span>
                          </div>
                        </>
                      )}
                      {!isSelected && (
                        <div style={{ color: '#4b5563', fontSize: 11 }}>Click to expand full post</div>
                      )}
                    </div>
                  )
                })}
              </div>
            ) : <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>Enter a topic and generate variations →</div>}
          </Card>
        </TwoCol>
      )}

    </PageShell>
  )
}
