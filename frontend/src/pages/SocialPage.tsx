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

  // ── Employee Advocacy Generator (Round 9) ──
  const ADVOCACY_TONES = [{ label: 'Professional', value: 'professional' }, { label: 'Casual & Warm', value: 'casual' }, { label: 'Excited / Celebratory', value: 'excited' }, { label: 'Humble & Grateful', value: 'humble' }]
  const EMPLOYEE_ROLES = [{ label: 'Founder / CEO', value: 'founder' }, { label: 'Sales / BD', value: 'sales' }, { label: 'Engineer', value: 'engineer' }, { label: 'HR / People', value: 'hr' }, { label: 'Marketing', value: 'marketing' }, { label: 'Team Member', value: 'team_member' }]
  // Influencer Outreach Generator (Round 11)
  const [ioInfluencer, setIoInfluencer] = useState('Neha Sharma')
  const [ioBrand, setIoBrand]           = useState('')
  const [ioNiche, setIoNiche]           = useState('lifestyle')
  const [ioPlatform, setIoPlatform]     = useState('instagram')
  const [ioFollowers, setIoFollowers]   = useState('75000')
  const [ioGoal, setIoGoal]             = useState('brand awareness')
  const [ioProduct, setIoProduct]       = useState('')
  const [ioBudget, setIoBudget]         = useState('')
  const [ioRes, setIoRes]               = useState<any>(null)
  const [ioLoading, setIoLoading]       = useState(false)
  const [ioErr, setIoErr]               = useState('')
  const [ioActiveEmail, setIoActiveEmail] = useState<'primary' | 'negotiation' | 'followup1' | 'followup2'>('primary')
  const runInfluencerOutreach = async () => {
    setIoLoading(true); setIoErr(''); setIoRes(null)
    try {
      setIoRes(await socialAction('influencer_outreach', {
        brand_name: ioBrand, influencer_name: ioInfluencer, influencer_niche: ioNiche,
        influencer_platform: ioPlatform, follower_count: parseInt(ioFollowers) || 75000,
        campaign_goal: ioGoal, product_name: ioProduct, budget_range: ioBudget,
        deliverables: ['1 feed post', '3 stories'], industry: ioNiche,
      }, ioPlatform))
    } catch (e: any) { setIoErr(e.message) }
    finally { setIoLoading(false) }
  }

  // Viral Hook Generator (Round 10)
  const [hookTopic, setHookTopic]       = useState('')
  const [hookBrand, setHookBrand]       = useState('')
  const [hookIndustry, setHookIndustry] = useState('')
  const [hookGoal, setHookGoal]         = useState('engagement')
  const [hookPlatforms, setHookPlatforms] = useState<string[]>(['linkedin', 'twitter'])
  const [hookRes, setHookRes]           = useState<any>(null)
  const [hookLoading, setHookLoading]   = useState(false)
  const [hookErr, setHookErr]           = useState('')
  const toggleHookPlatform = (p: string) => setHookPlatforms(prev => prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p])
  const runViralHooks = async () => {
    setHookLoading(true); setHookErr(''); setHookRes(null)
    try {
      const r = await socialAction('viral_hook_generator', {
        topic: hookTopic, brand_name: hookBrand, industry: hookIndustry,
        platforms: hookPlatforms, goal: hookGoal,
      }, hookPlatforms[0] || 'linkedin')
      setHookRes(r)
    } catch (e: any) { setHookErr(e.message) }
    finally { setHookLoading(false) }
  }

  const [advCompany, setAdvCompany]     = useState('')
  const [advNews, setAdvNews]           = useState('')
  const [advRole, setAdvRole]           = useState('founder')
  const [advIndustry, setAdvIndustry]   = useState('')
  const [advTone, setAdvTone]           = useState('professional')
  const [advVariants, setAdvVariants]   = useState('3')
  const [advPlatforms, setAdvPlatforms] = useState<string[]>(['linkedin'])
  const [advRes, setAdvRes]             = useState<any>(null)
  const [advLoading, setAdvLoading]     = useState(false)
  const [advErr, setAdvErr]             = useState('')

  const toggleAdvPlatform = (p: string) => setAdvPlatforms(prev => prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p])

  const runAdvocacy = async () => {
    setAdvLoading(true); setAdvErr(''); setAdvRes(null)
    try {
      setAdvRes(await socialAction('employee_advocacy', {
        company_name: advCompany, news_or_achievement: advNews, employee_role: advRole,
        industry: advIndustry, tone: advTone, platforms: advPlatforms,
        num_variants: parseInt(advVariants) || 3,
      }, advPlatforms[0] || 'linkedin'))
    } catch (e: any) { setAdvErr(e.message) }
    setAdvLoading(false)
  }

  // ── Competitor Content Spy (Round 8) ──
  const DEMO_COMPETITORS = [
    { name: 'CompetitorA', strengths: 'Daily Reels, strong CTA', weaknesses: 'No LinkedIn, no regional content', estimated_followers: 45000, avg_engagement: 4.2, top_content: 'Product demos + customer stories' },
    { name: 'CompetitorB', strengths: 'Thought leadership on LinkedIn', weaknesses: 'Inconsistent posting, no video', estimated_followers: 28000, avg_engagement: 2.8, top_content: 'Industry reports + CEO posts' },
    { name: 'CompetitorC', strengths: 'Heavy ad spend on Meta', weaknesses: 'Generic content, low organic reach', estimated_followers: 62000, avg_engagement: 1.1, top_content: 'Offer-based ads, discount posts' },
  ]
  const [spyBrand, setSpyBrand]         = useState('')
  const [spyIndustry, setSpyIndustry]   = useState('')
  const [spyJson, setSpyJson]           = useState(JSON.stringify(DEMO_COMPETITORS, null, 2))
  const [spyPlatforms, setSpyPlatforms] = useState<string[]>(['instagram', 'linkedin'])
  const [spyRes, setSpyRes]             = useState<any>(null)
  const [spyLoading, setSpyLoading]     = useState(false)
  const [spyErr, setSpyErr]             = useState('')

  const toggleSpyPlatform = (p: string) => setSpyPlatforms(prev => prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p])

  const runCompetitorSpy = async () => {
    setSpyLoading(true); setSpyErr(''); setSpyRes(null)
    try {
      let competitors: any[]
      try { competitors = JSON.parse(spyJson) } catch { throw new Error('Invalid JSON') }
      setSpyRes(await socialAction('competitor_spy', { brand_name: spyBrand, competitors, industry: spyIndustry, platforms: spyPlatforms }, 'all'))
    } catch (e: any) { setSpyErr(e.message) }
    setSpyLoading(false)
  }

  // ── Social ROI Dashboard (Round 7) ──
  const DEMO_ROI_CAMPAIGNS = [
    { platform: 'Meta', spend: 15000, impressions: 120000, clicks: 3600, leads: 180, conversions: 22, revenue: 110000 },
    { platform: 'Google', spend: 20000, impressions: 85000, clicks: 4250, leads: 212, conversions: 35, revenue: 175000 },
    { platform: 'LinkedIn', spend: 10000, impressions: 32000, clicks: 960, leads: 96, conversions: 8, revenue: 64000 },
  ]
  const [roiBrand, setRoiBrand]     = useState('')
  const [roiPeriod, setRoiPeriod]   = useState('January 2025')
  const [roiJson, setRoiJson]       = useState(JSON.stringify(DEMO_ROI_CAMPAIGNS, null, 2))
  const [roiRes, setRoiRes]         = useState<any>(null)
  const [roiLoading, setRoiLoading] = useState(false)
  const [roiErr, setRoiErr]         = useState('')

  const runSocialRoi = async () => {
    setRoiLoading(true); setRoiErr(''); setRoiRes(null)
    try {
      let campaigns: any[]
      try { campaigns = JSON.parse(roiJson) } catch { throw new Error('Invalid JSON') }
      setRoiRes(await socialAction('social_roi', { brand_name: roiBrand, campaigns, period: roiPeriod }, 'all'))
    } catch (e: any) { setRoiErr(e.message) }
    setRoiLoading(false)
  }

  // ── Brand Mention Responder (Round 6) ──
  const [mentBrand, setMentBrand]     = useState('')
  const [mentPlatform, setMentPlatform] = useState('twitter')
  const [mentLang, setMentLang]       = useState('en')
  const [mentMentions, setMentMentions] = useState(JSON.stringify([
    { id: 'M001', author: '@rahul_dev', text: 'Just tried @MentBrand and it is absolutely terrible! Lost 2 hours of data. Unacceptable!', sentiment: 'very negative', platform: 'twitter', timestamp: '2024-01-15T10:30:00Z', followers: 2400 },
    { id: 'M002', author: '@priya_cto', text: '@MentBrand your AI feature is 🔥 — saved our team 5 hours this week. Keep it up!', sentiment: 'positive', platform: 'twitter', timestamp: '2024-01-15T09:15:00Z', followers: 8900 },
    { id: 'M003', author: '@startup_guy', text: 'Thinking of switching to @MentBrand from Zoho. Anyone have experience?', sentiment: 'neutral', platform: 'twitter', timestamp: '2024-01-15T08:45:00Z', followers: 1200 },
  ], null, 2))
  const [mentRes, setMentRes]         = useState<any>(null)
  const [mentLoading, setMentLoading] = useState(false)
  const [mentErr, setMentErr]         = useState('')

  const runMentionResponder = async () => {
    setMentLoading(true); setMentErr(''); setMentRes(null)
    try {
      let mentions: any[]
      try { mentions = JSON.parse(mentMentions) } catch { throw new Error('Invalid JSON in mentions') }
      setMentRes(await socialAction('mention_responder', {
        brand_name: mentBrand, mentions, platform: mentPlatform,
      }, mentPlatform, mentLang))
    } catch (e: any) { setMentErr(e.message) }
    setMentLoading(false)
  }

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
          { id: 'abtest',     label: 'A/B Copy Tester',      icon: '🔬' },
          { id: 'mention',    label: 'Mention Responder',     icon: '📣' },
          { id: 'roi',        label: 'Social ROI',            icon: '📈' },
          { id: 'spy',        label: 'Competitor Spy',        icon: '🕵️' },
          { id: 'advocacy',   label: 'Employee Advocacy',     icon: '📢' },
          { id: 'hooks',      label: 'Viral Hooks',           icon: '🎣' },
          { id: 'outreach',   label: 'Influencer Outreach',   icon: '✉️' },
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

      {/* ── EMPLOYEE ADVOCACY GENERATOR (Round 9) ── */}
      {tab === 'advocacy' && (
        <TwoCol>
          <Card>
            <SectionHead title="Employee Advocacy Generator" sub="Turn company news into authentic personal posts — 10x organic reach" />
            <Input label="Company Name" value={advCompany} onChange={setAdvCompany} placeholder="e.g. Freshworks, Zoho" />
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>News / Achievement to share</div>
              <textarea value={advNews} onChange={e => setAdvNews(e.target.value)} rows={3}
                placeholder="e.g. We just crossed 10,000 customers! Our team of 45 people built a product used across 30 countries in 3 years."
                style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: 10, fontSize: 13, resize: 'vertical', boxSizing: 'border-box' }} />
            </div>
            <Select label="Employee Role / Persona" value={advRole} onChange={setAdvRole} options={EMPLOYEE_ROLES} />
            <Input label="Industry" value={advIndustry} onChange={setAdvIndustry} placeholder="e.g. SaaS, Fintech, Healthcare" />
            <Select label="Tone" value={advTone} onChange={setAdvTone} options={ADVOCACY_TONES} />
            <Select label="Number of Variants" value={advVariants} onChange={setAdvVariants} options={[{ label: '2 Variants', value: '2' }, { label: '3 Variants', value: '3' }, { label: '4 Variants', value: '4' }]} />
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 6 }}>Platforms</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {['linkedin', 'twitter', 'instagram', 'facebook'].map(p => (
                  <span key={p} onClick={() => toggleAdvPlatform(p)} style={{
                    padding: '4px 12px', borderRadius: 20, fontSize: 12, cursor: 'pointer',
                    background: advPlatforms.includes(p) ? 'rgba(79,142,247,0.15)' : 'transparent',
                    border: `1px solid ${advPlatforms.includes(p) ? 'rgba(79,142,247,0.5)' : '#1e2535'}`,
                    color: advPlatforms.includes(p) ? '#4f8ef7' : '#6b7280',
                  }}>{p.charAt(0).toUpperCase() + p.slice(1)}</span>
                ))}
              </div>
            </div>
            <Btn onClick={runAdvocacy} loading={advLoading} disabled={!advNews} style={{ width: '100%' }}>Generate Advocacy Posts</Btn>
            {advErr && <div style={{ color: '#f59e0b', fontSize: 11, marginTop: 8 }}>Demo mode: {advErr}</div>}
          </Card>
          <Card>
            <SectionHead title="Ready-to-Share Posts" sub="Each variant has a unique hook — pick the one that fits your voice" />
            {advRes ? (
              <>
                {advRes.persona_tip && (
                  <div style={{ background: '#0f172a', border: '1px solid #818cf833', borderRadius: 8, padding: '10px 14px', marginBottom: 14, fontSize: 12, color: '#818cf8' }}>
                    💡 <strong>Persona Tip:</strong> {advRes.persona_tip}
                  </div>
                )}
                {(advRes.variants || []).map((v: any, i: number) => (
                  <div key={i} style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 10, padding: 14, marginBottom: 12 }}>
                    <div style={{ color: '#f59e0b', fontSize: 13, fontWeight: 700, marginBottom: 6 }}>Variant {i + 1} — {v.hook}</div>
                    <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.8, whiteSpace: 'pre-wrap', marginBottom: 8 }}>{v.body}</div>
                    {v.cta && <div style={{ color: '#22c55e', fontSize: 12, marginBottom: 8, fontStyle: 'italic' }}>{v.cta}</div>}
                    {v.hashtags && (
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
                        {v.hashtags.map((h: string, j: number) => (
                          <span key={j} style={{ fontSize: 11, padding: '2px 8px', background: '#1e2535', color: '#818cf8', borderRadius: 6 }}>{h}</span>
                        ))}
                      </div>
                    )}
                    {v.engagement_tip && <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 8 }}>📊 {v.engagement_tip}</div>}
                    <span onClick={() => navigator.clipboard?.writeText(`${v.hook}\n\n${v.body}\n\n${v.cta || ''}\n\n${(v.hashtags || []).join(' ')}`)}
                      style={{ cursor: 'pointer', fontSize: 11, padding: '3px 10px', background: '#374151', color: '#fff', borderRadius: 6 }}>Copy Post</span>
                  </div>
                ))}
                <div style={{ marginTop: 4 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#e2e8f0', marginBottom: 6 }}>Best Practices</div>
                  {(advRes.best_practice || []).map((b: string, i: number) => (
                    <div key={i} style={{ fontSize: 11, color: '#6b7280', padding: '4px 0', borderBottom: '1px solid #0f1117' }}>→ {b}</div>
                  ))}
                </div>
              </>
            ) : <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>Add news/achievement and click Generate →</div>}
          </Card>
        </TwoCol>
      )}

      {/* ── COMPETITOR CONTENT SPY (Round 8) ── */}
      {tab === 'spy' && (
        <TwoCol>
          <Card>
            <SectionHead title="Competitor Content Spy" sub="Find gaps in competitor strategy — then own them" />
            <Input label="Your Brand Name" value={spyBrand} onChange={setSpyBrand} placeholder="e.g. Freshworks" />
            <Input label="Industry" value={spyIndustry} onChange={setSpyIndustry} placeholder="e.g. B2B SaaS, CA Firm, Retail" />
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 6 }}>Platforms to analyse</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {['instagram','linkedin','twitter','facebook','youtube'].map(p => (
                  <span key={p} onClick={() => toggleSpyPlatform(p)} style={{
                    padding: '4px 12px', borderRadius: 20, fontSize: 12, cursor: 'pointer',
                    background: spyPlatforms.includes(p) ? 'rgba(79,142,247,0.15)' : 'transparent',
                    border: `1px solid ${spyPlatforms.includes(p) ? 'rgba(79,142,247,0.5)' : '#1e2535'}`,
                    color: spyPlatforms.includes(p) ? '#4f8ef7' : '#6b7280',
                  }}>{p.charAt(0).toUpperCase() + p.slice(1)}</span>
                ))}
              </div>
            </div>
            <div style={{ marginBottom: 6, fontSize: 12, color: '#9ca3af' }}>Competitor Profiles JSON</div>
            <textarea value={spyJson} onChange={e => setSpyJson(e.target.value)} rows={10}
              style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: 10, fontSize: 11, fontFamily: 'monospace', resize: 'vertical', boxSizing: 'border-box' }} />
            <Btn onClick={runCompetitorSpy} loading={spyLoading} style={{ marginTop: 12, width: '100%' }}>Spy & Find Gaps</Btn>
            {spyErr && <div style={{ color: '#f59e0b', fontSize: 11, marginTop: 8 }}>Demo mode: {spyErr}</div>}
          </Card>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {spyRes ? (
              <>
                {/* Summary */}
                <Card>
                  <div style={{ background: '#0f172a', border: '1px solid #818cf833', borderRadius: 8, padding: '12px 16px', marginBottom: 12 }}>
                    <div style={{ fontSize: 13, color: '#818cf8', fontWeight: 600, marginBottom: 4 }}>Key Insight</div>
                    <div style={{ color: '#e2e8f0', fontSize: 13 }}>{spyRes.summary}</div>
                  </div>
                  <div style={{ display: 'flex', gap: 10 }}>
                    <div style={{ flex: 1, background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: '10px 12px', textAlign: 'center' }}>
                      <div style={{ fontSize: 20, fontWeight: 700, color: '#ef4444' }}>{spyRes.competitors_analyzed}</div>
                      <div style={{ fontSize: 11, color: '#6b7280' }}>Competitors Scanned</div>
                    </div>
                    <div style={{ flex: 1, background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: '10px 12px', textAlign: 'center' }}>
                      <div style={{ fontSize: 20, fontWeight: 700, color: '#22c55e' }}>{spyRes.content_gaps?.length || 0}</div>
                      <div style={{ fontSize: 11, color: '#6b7280' }}>Content Gaps Found</div>
                    </div>
                    <div style={{ flex: 1, background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: '10px 12px', textAlign: 'center' }}>
                      <div style={{ fontSize: 20, fontWeight: 700, color: '#f59e0b' }}>{spyRes.avg_competitor_engagement}%</div>
                      <div style={{ fontSize: 11, color: '#6b7280' }}>Avg Competitor Eng.</div>
                    </div>
                  </div>
                </Card>

                {/* Content Gaps */}
                <Card>
                  <SectionHead title="Content Gaps to Own" sub="What competitors are NOT doing" />
                  {(spyRes.content_gaps || []).map((g: any, i: number) => (
                    <div key={i} style={{ background: '#0f1117', border: `1px solid ${g.priority === 'High' ? '#22c55e' : '#f59e0b'}33`, borderRadius: 8, padding: 12, marginBottom: 8 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{ fontWeight: 600, color: '#e2e8f0', fontSize: 13 }}>🎯 {g.gap}</span>
                        <Badge label={g.priority} color={g.priority === 'High' ? '#22c55e' : '#f59e0b'} />
                      </div>
                      <div style={{ fontSize: 12, color: '#9ca3af' }}>{g.opportunity}</div>
                    </div>
                  ))}
                </Card>

                {/* Counter strategy */}
                <Card>
                  <SectionHead title="Counter-Content Strategy" sub="Platform-specific plan" />
                  {(spyRes.counter_strategy || []).map((s: any, i: number) => (
                    <div key={i} style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: 12, marginBottom: 8 }}>
                      <div style={{ fontWeight: 600, color: '#818cf8', fontSize: 13, marginBottom: 6 }}>{s.platform.charAt(0).toUpperCase() + s.platform.slice(1)}</div>
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 6 }}>
                        <Badge label={`📅 ${s.post_frequency}`} color="#6b7280" />
                        <Badge label={`⏰ ${s.best_posting_time}`} color="#6b7280" />
                        <Badge label={`🎬 ${s.top_format}`} color="#4f8ef7" />
                      </div>
                      <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 4 }}>Recommended themes:</div>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {(s.recommended_themes || []).map((t: string, j: number) => (
                          <span key={j} style={{ fontSize: 11, padding: '2px 8px', background: '#1e2535', color: '#9ca3af', borderRadius: 6 }}>{t}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </Card>

                {/* 90-day seeds */}
                <Card>
                  <SectionHead title="90-Day Content Seeds" sub="Ready-to-use post ideas" />
                  {(spyRes.calendar_seeds || []).map((s: any, i: number) => (
                    <div key={i} style={{ padding: '8px 0', borderBottom: '1px solid #0f1117', fontSize: 12 }}>
                      <div style={{ display: 'flex', gap: 6, marginBottom: 3 }}>
                        <Badge label={s.platform} color="#818cf8" />
                        <Badge label={s.week} color="#6b7280" />
                        <Badge label={s.format} color="#4f8ef7" />
                      </div>
                      <div style={{ color: '#e2e8f0' }}>{s.post}</div>
                      <div style={{ color: '#6b7280', fontSize: 11, marginTop: 2 }}>Gap addressed: {s.gap_addressed}</div>
                    </div>
                  ))}
                </Card>
              </>
            ) : <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>Add competitor profiles and click Spy & Find Gaps →</div>}
          </div>
        </TwoCol>
      )}

      {/* ── SOCIAL ROI DASHBOARD (Round 7) ── */}
      {tab === 'roi' && (
        <TwoCol>
          <Card>
            <SectionHead title="Social ROI Dashboard" sub="Calculate ROAS, CPL, CPA across all ad platforms" />
            <Input label="Brand / Company" value={roiBrand} onChange={setRoiBrand} placeholder="e.g. Freshworks" />
            <Input label="Period" value={roiPeriod} onChange={setRoiPeriod} placeholder="e.g. January 2025" />
            <div style={{ marginBottom: 6, fontSize: 12, color: '#9ca3af' }}>Campaigns JSON (spend, impressions, clicks, leads, conversions, revenue per platform)</div>
            <textarea value={roiJson} onChange={e => setRoiJson(e.target.value)} rows={12}
              style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: 10, fontSize: 12, fontFamily: 'monospace', resize: 'vertical', boxSizing: 'border-box' }} />
            <Btn onClick={runSocialRoi} loading={roiLoading} style={{ marginTop: 12, width: '100%' }}>Calculate ROI</Btn>
            {roiErr && <div style={{ color: '#f59e0b', fontSize: 11, marginTop: 8 }}>Demo mode: {roiErr}</div>}
          </Card>
          <Card>
            <SectionHead title="ROI Results" sub="Platform breakdown & recommendations" />
            {roiRes ? (() => {
              const t = roiRes.totals || {}
              const GRADE_COLOR: Record<string, string> = { Excellent: '#10b981', Good: '#22c55e', Average: '#f59e0b', Poor: '#ef4444' }
              return (
                <>
                  {/* Overall KPIs */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginBottom: 18 }}>
                    {[
                      { label: 'Total Spend', val: `₹${(t.spend || 0).toLocaleString('en-IN')}`, color: '#e2e8f0' },
                      { label: 'Total Revenue', val: `₹${(t.revenue || 0).toLocaleString('en-IN')}`, color: '#22c55e' },
                      { label: 'Overall ROAS', val: `${t.roas || 0}x`, color: t.roas >= 2 ? '#10b981' : '#ef4444' },
                      { label: 'Total Leads', val: t.leads || 0, color: '#818cf8' },
                      { label: 'CPL', val: `₹${(t.cpl || 0).toLocaleString('en-IN')}`, color: '#e2e8f0' },
                      { label: 'ROI', val: `${t.roi_pct || 0}%`, color: (t.roi_pct || 0) >= 0 ? '#22c55e' : '#ef4444' },
                    ].map(k => (
                      <div key={k.label} style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: '10px 12px', textAlign: 'center' }}>
                        <div style={{ fontSize: 16, fontWeight: 700, color: k.color, fontVariantNumeric: 'tabular-nums' }}>{k.val}</div>
                        <div style={{ fontSize: 11, color: '#6b7280' }}>{k.label}</div>
                      </div>
                    ))}
                  </div>

                  {/* Platform table */}
                  <div style={{ overflowX: 'auto', marginBottom: 18 }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                      <thead>
                        <tr style={{ color: '#6b7280', borderBottom: '1px solid #1e2535' }}>
                          {['Platform', 'Spend', 'Revenue', 'ROAS', 'CPL', 'CPA', 'CTR%', 'Grade'].map(h => (
                            <th key={h} style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600 }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {(roiRes.platforms || []).map((p: any, i: number) => (
                          <tr key={i} style={{ borderBottom: '1px solid #0f1117' }}>
                            <td style={{ padding: '7px 8px', color: '#e2e8f0', fontWeight: 600 }}>{p.platform}</td>
                            <td style={{ padding: '7px 8px', color: '#9ca3af', fontVariantNumeric: 'tabular-nums' }}>₹{(p.spend || 0).toLocaleString('en-IN')}</td>
                            <td style={{ padding: '7px 8px', color: '#22c55e', fontVariantNumeric: 'tabular-nums' }}>₹{(p.revenue || 0).toLocaleString('en-IN')}</td>
                            <td style={{ padding: '7px 8px', color: p.roas >= 2 ? '#10b981' : '#ef4444', fontWeight: 700 }}>{p.roas}x</td>
                            <td style={{ padding: '7px 8px', color: '#9ca3af' }}>₹{(p.cpl || 0).toLocaleString('en-IN')}</td>
                            <td style={{ padding: '7px 8px', color: '#9ca3af' }}>₹{(p.cpa || 0).toLocaleString('en-IN')}</td>
                            <td style={{ padding: '7px 8px', color: '#9ca3af' }}>{p.ctr}%</td>
                            <td style={{ padding: '7px 8px' }}><Badge label={p.grade} color={GRADE_COLOR[p.grade] || '#6b7280'} /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Recommendations */}
                  {(roiRes.recommendations || []).length > 0 && (
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', marginBottom: 8 }}>AI Recommendations</div>
                      {roiRes.recommendations.map((r: string, i: number) => (
                        <div key={i} style={{ display: 'flex', gap: 8, padding: '7px 0', borderBottom: '1px solid #0f1117', fontSize: 12, color: '#9ca3af' }}>
                          <span style={{ color: '#818cf8', flexShrink: 0 }}>→</span>{r}
                        </div>
                      ))}
                    </div>
                  )}
                  <div style={{ marginTop: 12, display: 'flex', gap: 10 }}>
                    <div style={{ fontSize: 12, color: '#6b7280' }}>Best: <span style={{ color: '#22c55e', fontWeight: 600 }}>{roiRes.best_platform}</span></div>
                    <div style={{ fontSize: 12, color: '#6b7280' }}>Review: <span style={{ color: '#f59e0b', fontWeight: 600 }}>{roiRes.worst_platform}</span></div>
                  </div>
                </>
              )
            })() : <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>Enter campaign data and click Calculate ROI →</div>}
          </Card>
        </TwoCol>
      )}

      {/* ── BRAND MENTION RESPONDER (Round 6) ── */}
      {tab === 'mention' && (
        <TwoCol>
          <Card>
            <SectionHead title="Brand Mention Responder" sub="AI drafts replies to every brand mention — negative, positive, or neutral" />
            <Input label="Brand / Company Name" value={mentBrand} onChange={setMentBrand} placeholder="e.g. Zoho, Freshworks" />
            <Select label="Primary Platform" value={mentPlatform} onChange={setMentPlatform} options={[
              { label: 'Twitter / X', value: 'twitter' }, { label: 'LinkedIn', value: 'linkedin' },
              { label: 'Instagram', value: 'instagram' }, { label: 'Facebook', value: 'facebook' },
            ]} />
            <Select label="Response Language" value={mentLang} onChange={setMentLang} options={LANG_OPTIONS} />
            <div style={{ marginBottom: 6, fontSize: 12, color: '#9ca3af' }}>Mentions JSON (paste or edit)</div>
            <textarea
              value={mentMentions}
              onChange={e => setMentMentions(e.target.value)}
              rows={10}
              style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: 10, fontSize: 12, fontFamily: 'monospace', resize: 'vertical', boxSizing: 'border-box' }}
            />
            <Btn onClick={runMentionResponder} loading={mentLoading} disabled={!mentBrand} style={{ marginTop: 12, width: '100%' }}>
              Generate AI Responses
            </Btn>
            {mentErr && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{mentErr}</div>}
          </Card>
          <Card>
            <SectionHead title="AI-Drafted Responses" sub="Review and post — personalized per sentiment" />
            {mentRes ? (() => {
              const summary = mentRes.summary || {}
              const responses: any[] = mentRes.responses || []
              const SENT_COLOR: Record<string, string> = {
                'very negative': '#ef4444', 'negative': '#f97316', 'neutral': '#6b7280',
                'positive': '#22c55e', 'very positive': '#10b981',
              }
              return (
                <>
                  {/* KPI bar */}
                  <div style={{ display: 'flex', gap: 12, marginBottom: 18, flexWrap: 'wrap' }}>
                    {[
                      { label: 'Total Mentions', val: summary.total_mentions ?? responses.length },
                      { label: 'Urgent', val: summary.urgent_count ?? responses.filter((r: any) => r.urgency === 'high').length, color: '#ef4444' },
                      { label: 'Positive', val: summary.positive_count ?? responses.filter((r: any) => r.sentiment === 'positive' || r.sentiment === 'very positive').length, color: '#22c55e' },
                    ].map(k => (
                      <div key={k.label} style={{ flex: 1, minWidth: 90, background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: '10px 14px' }}>
                        <div style={{ fontSize: 20, fontWeight: 700, color: k.color || '#e2e8f0' }}>{k.val}</div>
                        <div style={{ fontSize: 11, color: '#6b7280' }}>{k.label}</div>
                      </div>
                    ))}
                  </div>

                  {/* Response cards */}
                  {responses.map((r: any, i: number) => (
                    <div key={i} style={{ background: '#0f1117', border: `1px solid ${SENT_COLOR[r.sentiment] || '#1e2535'}44`, borderRadius: 10, padding: 14, marginBottom: 12 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                        <span style={{ fontWeight: 600, color: '#e2e8f0', fontSize: 13 }}>{r.author || `@mention_${i + 1}`}</span>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <Badge label={r.sentiment} color={SENT_COLOR[r.sentiment] || '#6b7280'} />
                          {r.urgency === 'high' && <Badge label="URGENT" color="#ef4444" />}
                        </div>
                      </div>
                      <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 8, fontStyle: 'italic' }}>"{r.original_text?.slice(0, 120)}{(r.original_text?.length || 0) > 120 ? '…' : ''}"</div>
                      <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.7, background: '#111827', borderRadius: 6, padding: '8px 12px', marginBottom: 8, whiteSpace: 'pre-wrap' }}>{r.ai_response}</div>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {r.tone && <Badge label={`Tone: ${r.tone}`} color="#818cf8" />}
                        {r.action_required && <Badge label={r.action_required} color="#f59e0b" />}
                        <span onClick={() => navigator.clipboard?.writeText(r.ai_response)} style={{ cursor: 'pointer', color: '#fff', fontSize: 11, padding: '3px 10px', background: '#374151', borderRadius: 6, marginLeft: 'auto' }}>Copy</span>
                      </div>
                    </div>
                  ))}
                  {mentRes.brand_health_score !== undefined && (
                    <div style={{ marginTop: 12, background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: '10px 14px' }}>
                      <div style={{ fontSize: 12, color: '#9ca3af' }}>Brand Sentiment Score</div>
                      <div style={{ fontSize: 24, fontWeight: 700, color: mentRes.brand_health_score >= 60 ? '#22c55e' : mentRes.brand_health_score >= 40 ? '#f59e0b' : '#ef4444' }}>{mentRes.brand_health_score}/100</div>
                    </div>
                  )}
                </>
              )
            })() : <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>Paste mentions JSON and click Generate →</div>}
          </Card>
        </TwoCol>
      )}

      {/* ── INFLUENCER OUTREACH GENERATOR (Round 11) ── */}
      {tab === 'outreach' && (
        <TwoCol>
          <Card>
            <SectionHead title="✉️ Influencer Outreach Kit" sub="Personalized pitch + negotiation + follow-up sequence" />
            <Input label="Influencer Name" value={ioInfluencer} onChange={setIoInfluencer} placeholder="e.g. Neha Sharma" />
            <Input label="Your Brand Name" value={ioBrand} onChange={setIoBrand} placeholder="e.g. Mamaearth, Zoho" />
            <Input label="Influencer Niche" value={ioNiche} onChange={setIoNiche} placeholder="e.g. lifestyle, tech, finance, fitness" />
            <Select label="Platform" value={ioPlatform} onChange={setIoPlatform} options={[
              { label: 'Instagram', value: 'instagram' },
              { label: 'YouTube', value: 'youtube' },
              { label: 'LinkedIn', value: 'linkedin' },
              { label: 'Twitter/X', value: 'twitter' },
              { label: 'Moj / Josh', value: 'moj' },
            ]} />
            <Input label="Follower Count" value={ioFollowers} onChange={setIoFollowers} placeholder="e.g. 75000" />
            <Select label="Campaign Goal" value={ioGoal} onChange={setIoGoal} options={[
              { label: 'Brand Awareness', value: 'brand awareness' },
              { label: 'Product Launch', value: 'product launch' },
              { label: 'Lead Generation', value: 'lead generation' },
              { label: 'App Downloads', value: 'app downloads' },
              { label: 'Sales / Conversions', value: 'sales and conversions' },
            ]} />
            <Input label="Product / Service to Feature" value={ioProduct} onChange={setIoProduct} placeholder="e.g. AI accounting software" />
            <Input label="Budget Range (optional)" value={ioBudget} onChange={setIoBudget} placeholder="e.g. ₹20K–₹40K per post" />
            <Btn onClick={runInfluencerOutreach} loading={ioLoading}>Generate Outreach Kit</Btn>
            {ioErr && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{ioErr}</div>}
          </Card>
          <Card>
            {ioRes ? (() => {
              const r = ioRes
              const tierColor = r.tier === 'mega' ? '#a78bfa' : r.tier === 'macro' ? '#818cf8' : r.tier === 'micro' ? '#10b981' : '#6b7280'
              const emails: Record<string, { label: string; content: string }> = {
                primary:     { label: 'Initial Outreach', content: r.primary_outreach_email },
                negotiation: { label: 'Negotiation Reply', content: r.negotiation_email },
                followup1:   { label: `Follow-up (Day ${r.follow_up_sequence?.[0]?.day || 3})`, content: r.follow_up_sequence?.[0]?.body || '' },
                followup2:   { label: `Follow-up (Day ${r.follow_up_sequence?.[1]?.day || 7})`, content: r.follow_up_sequence?.[1]?.body || '' },
              }
              return (
                <>
                  {/* Tier + Rate badges */}
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
                    <Badge label={`${r.tier?.toUpperCase()} tier — ${r.tier_range} followers`} color={tierColor} />
                    <Badge label={`Post rate: ${r.market_rate_post}`} color="#f59e0b" />
                    <Badge label={`Reel rate: ${r.market_rate_reel}`} color="#f97316" />
                  </div>
                  {r.negotiation_tip && <div style={{ fontSize: 12, color: '#10b981', background: 'rgba(16,185,129,0.08)', borderRadius: 6, padding: '8px 12px', marginBottom: 14 }}>💡 {r.negotiation_tip}</div>}

                  {/* Email switcher */}
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
                    {(Object.entries(emails) as [string, { label: string; content: string }][]).map(([key, val]) => (
                      <span key={key} onClick={() => setIoActiveEmail(key as any)} style={{
                        padding: '4px 12px', borderRadius: 20, fontSize: 12, cursor: 'pointer',
                        background: ioActiveEmail === key ? '#10b981' : '#1e2535',
                        color: ioActiveEmail === key ? '#fff' : '#9ca3af',
                        border: `1px solid ${ioActiveEmail === key ? '#10b981' : '#374151'}`,
                      }}>{val.label}</span>
                    ))}
                  </div>

                  {/* Subject line */}
                  {ioActiveEmail === 'primary' && r.follow_up_sequence && (
                    <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 6 }}>
                      Subject: <span style={{ color: '#e2e8f0' }}>{r.primary_outreach_email?.split('\n')[0]?.replace('Subject: ', '')}</span>
                    </div>
                  )}

                  {/* Email body */}
                  <div style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: '12px 14px', fontSize: 13, color: '#e2e8f0', lineHeight: 1.7, whiteSpace: 'pre-wrap', maxHeight: 360, overflowY: 'auto', marginBottom: 10 }}>
                    {emails[ioActiveEmail]?.content}
                  </div>
                  <span onClick={() => navigator.clipboard?.writeText(emails[ioActiveEmail]?.content || '')} style={{ cursor: 'pointer', color: '#fff', fontSize: 12, padding: '5px 14px', background: '#374151', borderRadius: 6, display: 'inline-block', marginBottom: 14 }}>Copy Email</span>

                  {/* Campaign Brief */}
                  {(r.campaign_brief_outline || []).length > 0 && (
                    <div style={{ marginBottom: 14 }}>
                      <div style={{ fontSize: 12, fontWeight: 700, color: '#9ca3af', marginBottom: 8 }}>Campaign Brief Outline</div>
                      {r.campaign_brief_outline.map((line: string, i: number) => (
                        <div key={i} style={{ fontSize: 12, color: '#6b7280', background: '#0f1117', borderRadius: 4, padding: '5px 10px', marginBottom: 4 }}>{line}</div>
                      ))}
                    </div>
                  )}

                  {/* Do/Don't */}
                  {r.do_dont && (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                      <div>
                        <div style={{ fontSize: 11, fontWeight: 700, color: '#22c55e', marginBottom: 6 }}>DO ✓</div>
                        {(r.do_dont.do || []).map((d: string, i: number) => <div key={i} style={{ fontSize: 11, color: '#6b7280', marginBottom: 4 }}>• {d}</div>)}
                      </div>
                      <div>
                        <div style={{ fontSize: 11, fontWeight: 700, color: '#ef4444', marginBottom: 6 }}>DON'T ✗</div>
                        {(r.do_dont.dont || []).map((d: string, i: number) => <div key={i} style={{ fontSize: 11, color: '#6b7280', marginBottom: 4 }}>• {d}</div>)}
                      </div>
                    </div>
                  )}
                </>
              )
            })() : (
              <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>
                Fill in the influencer details and click Generate Outreach Kit →
              </div>
            )}
          </Card>
        </TwoCol>
      )}

      {/* ── VIRAL HOOK GENERATOR (Round 10) ── */}
      {tab === 'hooks' && (
        <TwoCol>
          <Card>
            <SectionHead title="🎣 Viral Hook Generator" sub="8 proven hook formulas that boost CTR up to 41%" />
            <Input label="Topic / Content Idea" value={hookTopic} onChange={setHookTopic} placeholder="e.g. GST compliance, AI automation, hiring tips" />
            <Input label="Brand Name" value={hookBrand} onChange={setHookBrand} placeholder="e.g. Zoho, your startup name" />
            <Input label="Industry" value={hookIndustry} onChange={setHookIndustry} placeholder="e.g. SaaS, Fintech, D2C" />
            <Select label="Goal" value={hookGoal} onChange={setHookGoal} options={[
              { label: 'Engagement (likes, comments)', value: 'engagement' },
              { label: 'Clicks & Traffic', value: 'clicks' },
              { label: 'Lead Generation', value: 'leads' },
              { label: 'Brand Awareness', value: 'awareness' },
              { label: 'Thought Leadership', value: 'thought_leadership' },
            ]} />
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 6 }}>Target Platforms</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {['linkedin', 'twitter', 'instagram', 'facebook', 'youtube', 'whatsapp'].map(p => (
                  <span key={p} onClick={() => toggleHookPlatform(p)} style={{
                    padding: '4px 10px', borderRadius: 20, fontSize: 12, cursor: 'pointer',
                    background: hookPlatforms.includes(p) ? 'rgba(16,185,129,0.15)' : '#1e2535',
                    border: `1px solid ${hookPlatforms.includes(p) ? '#10b981' : '#374151'}`,
                    color: hookPlatforms.includes(p) ? '#5eead4' : '#9ca3af',
                  }}>{p}</span>
                ))}
              </div>
            </div>
            <Btn onClick={runViralHooks} loading={hookLoading}>Generate Viral Hooks</Btn>
            {hookErr && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{hookErr}</div>}
          </Card>
          <Card>
            <SectionHead title="Hook Formulas" sub="Ranked by platform fit — click any variant to copy" />
            {hookRes ? (() => {
              const r = hookRes
              return (
                <>
                  {r.top_hook_text && (
                    <div style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid #10b981', borderRadius: 8, padding: '12px 14px', marginBottom: 16 }}>
                      <div style={{ fontSize: 11, color: '#10b981', fontWeight: 700, marginBottom: 4 }}>⭐ TOP PICK — {r.top_pick}</div>
                      <div style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600, lineHeight: 1.5 }}>{r.top_hook_text}</div>
                      <span onClick={() => navigator.clipboard?.writeText(r.top_hook_text)} style={{ display: 'inline-block', marginTop: 8, cursor: 'pointer', color: '#fff', fontSize: 11, padding: '3px 10px', background: '#374151', borderRadius: 6 }}>Copy</span>
                    </div>
                  )}
                  {(r.hooks || []).map((h: any, i: number) => (
                    <div key={i} style={{ background: '#111827', border: `1px solid ${h.recommended ? '#1e3a5f' : '#1e2535'}`, borderRadius: 8, padding: '12px 14px', marginBottom: 10 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                        <span style={{ color: '#a78bfa', fontSize: 13, fontWeight: 700 }}>{h.formula}</span>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <Badge label={h.ctr_boost} color="#22c55e" />
                          <Badge label={h.platform_fit + ' fit'} color={h.recommended ? '#10b981' : '#f59e0b'} />
                        </div>
                      </div>
                      <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600, marginBottom: 6 }}>{h.main_hook}</div>
                      <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 8, fontStyle: 'italic' }}>"{h.psychology}"</div>
                      {(h.variants || []).map((v: string, j: number) => (
                        <div key={j} onClick={() => navigator.clipboard?.writeText(v)} style={{ fontSize: 12, color: '#9ca3af', background: '#0f1117', borderRadius: 4, padding: '6px 10px', marginBottom: 4, cursor: 'pointer' }} title="Click to copy">↪ {v}</div>
                      ))}
                      <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                        <span style={{ fontSize: 11, color: '#4b5563' }}>Best for:</span>
                        {(h.best_for || []).map((bp: string) => <Badge key={bp} label={bp} color="#6b7280" />)}
                      </div>
                    </div>
                  ))}
                  {r.platform_tips && (
                    <div style={{ marginTop: 12, background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: '12px 14px' }}>
                      <div style={{ fontSize: 12, fontWeight: 700, color: '#9ca3af', marginBottom: 8 }}>Platform Writing Tips</div>
                      {Object.entries(r.platform_tips).map(([plat, tip]: [string, any]) => (
                        <div key={plat} style={{ marginBottom: 8 }}>
                          <div style={{ fontSize: 11, color: '#10b981', fontWeight: 600, textTransform: 'uppercase' }}>{plat}</div>
                          <div style={{ fontSize: 12, color: '#6b7280' }}>{tip}</div>
                        </div>
                      ))}
                    </div>
                  )}
                  {r.pro_tip && <div style={{ marginTop: 12, fontSize: 12, color: '#f59e0b', background: 'rgba(245,158,11,0.08)', borderRadius: 6, padding: '8px 12px' }}>💡 {r.pro_tip}</div>}
                </>
              )
            })() : (
              <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>
                Enter your topic and click Generate Viral Hooks →<br /><br />
                <span style={{ fontSize: 11, color: '#374151' }}>Demo topics: "AI automation", "GST compliance", "Instagram growth"</span>
              </div>
            )}
          </Card>
        </TwoCol>
      )}

    </PageShell>
  )
}
