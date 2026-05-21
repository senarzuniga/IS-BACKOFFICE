from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


THIS_FILE = Path(__file__).resolve()
SOURCE_REPO = THIS_FILE.parents[1]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_file(src: Path, dst: Path) -> bool:
    if not src.exists() or not src.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def copy_tree(src: Path, dst: Path) -> bool:
    if not src.exists() or not src.is_dir():
        return False
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return True


def insert_after(text: str, anchor: str, addition: str) -> str:
    if addition.strip() in text:
        return text
    idx = text.find(anchor)
    if idx == -1:
        return text
    pos = idx + len(anchor)
    return text[:pos] + addition + text[pos:]


def insert_before(text: str, anchor: str, addition: str) -> str:
    if addition.strip() in text:
        return text
    idx = text.find(anchor)
    if idx == -1:
        return text
    return text[:idx] + addition + text[idx:]


def patch_app_tsx(target_repo: Path) -> None:
    app_path = target_repo / "src" / "App.tsx"
    content = app_path.read_text(encoding="utf-8")

    content = insert_after(
        content,
        'import BusinessIntelligencePage from "./pages/BusinessIntelligencePage";\n',
        'import IngTradeLandingPage from "./pages/IngTradeLandingPage";\n',
    )

    content = insert_before(
        content,
        '                <Route path="/social-media" element={<SocialMediaSettingsPage />} />\n',
        '                <Route path="/ing-trade" element={<IngTradeLandingPage />} />\n',
    )

    app_path.write_text(content, encoding="utf-8")


def patch_sidebar(target_repo: Path) -> None:
    sidebar_path = target_repo / "src" / "components" / "AppSidebar.tsx"
    content = sidebar_path.read_text(encoding="utf-8")

    content = insert_after(
        content,
        '  SearchCheck,\n',
        '  Factory,\n',
    )

    new_nav_line = "    { title: language === 'es' ? 'Ing_TRADE' : 'Ing_TRADE', url: '/ing-trade', icon: Factory },\n"
    content = insert_before(
        content,
        "    { title: t.nav.socialMedia, url: '/social-media', icon: Share2 },\n",
        new_nav_line,
    )

    sidebar_path.write_text(content, encoding="utf-8")


def patch_dashboard(target_repo: Path) -> None:
    dashboard_path = target_repo / "src" / "pages" / "DashboardPage.tsx"
    content = dashboard_path.read_text(encoding="utf-8")

    content = insert_after(
        content,
        "import { Card, CardContent } from '@/components/ui/card';\n",
        "import { IngTradePromoBlock } from '@/components/ingtrade/IngTradePromoBlock';\n",
    )

    block = "\n      <div className=\"mt-8\">\n        <IngTradePromoBlock onOpen={() => navigate('/ing-trade')} />\n      </div>\n"
    content = insert_before(content, "    </div>\n  );\n};\n", block)

    dashboard_path.write_text(content, encoding="utf-8")


def create_react_files(target_repo: Path) -> None:
    promo_component = """import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowRight, BriefcaseBusiness } from 'lucide-react';

interface IngTradePromoBlockProps {
  onOpen: () => void;
}

export function IngTradePromoBlock({ onOpen }: IngTradePromoBlockProps) {
  return (
    <Card className=\"border-primary/30 bg-primary/5\">
      <CardContent className=\"py-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4\">
        <div>
          <p className=\"text-xs uppercase tracking-wide text-primary font-semibold\">New Business Vertical</p>
          <h4 className=\"text-lg font-semibold text-foreground flex items-center gap-2\">
            <BriefcaseBusiness className=\"h-5 w-5 text-primary\" />
            Ing_TRADE Used Machinery Business
          </h4>
          <p className=\"text-sm text-muted-foreground\">
            Landing, service portfolio, sales toolkit, and downloadable business kit are now available.
          </p>
        </div>
        <Button onClick={onOpen} className=\"gap-2\">
          Open Ing_TRADE
          <ArrowRight className=\"h-4 w-4\" />
        </Button>
      </CardContent>
    </Card>
  );
}
"""

    landing_page = """import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Building2, Globe2, PackageSearch, FileText, ArrowUpRight } from 'lucide-react';

const docs = [
  {
    label: 'Business Kit Folder',
    href: '/ing-trade/business-kit/',
    note: 'Complete operational folder exported from Ing_TRADE research.',
  },
  {
    label: 'Machine Trading Company View (CSV)',
    href: '/ing-trade/business-kit/intelligence/machine_trading_company_view.csv',
    note: 'Prioritized channels and accounts for sourcing and trading.',
  },
  {
    label: 'Business Presentation',
    href: '/ing-trade/business-kit/sales_assets/Ing_TRADE_Business_Presentation.pptx',
    note: 'Commercial deck for partner and customer conversations.',
  },
  {
    label: 'Offer Template',
    href: '/ing-trade/business-kit/sales_assets/templates/ING_TRADE_Offer_Template.docx',
    note: 'Reusable template for commercial proposals.',
  },
];

export default function IngTradeLandingPage() {
  return (
    <div className=\"p-6 lg:p-8 max-w-7xl mx-auto space-y-8\">
      <section className=\"space-y-3\">
        <Badge variant=\"outline\">Ing_TRADE</Badge>
        <h1 className=\"text-3xl lg:text-4xl font-bold tracking-tight\">Used Machinery Trading Business</h1>
        <p className=\"text-muted-foreground max-w-3xl\">
          Dedicated operating model for sourcing, qualifying, selling, and scaling used equipment
          opportunities across fruit packaging lines and flexo folder gluer ecosystems.
        </p>
      </section>

      <section className=\"grid grid-cols-1 md:grid-cols-3 gap-4\">
        <Card>
          <CardHeader>
            <CardTitle className=\"flex items-center gap-2 text-lg\"><Building2 className=\"h-5 w-5 text-primary\" /> Model</CardTitle>
            <CardDescription>Productized commercial framework</CardDescription>
          </CardHeader>
          <CardContent className=\"text-sm text-muted-foreground\">
            Structured around sourcing, valuation, deal execution, and partner channels.
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className=\"flex items-center gap-2 text-lg\"><PackageSearch className=\"h-5 w-5 text-primary\" /> Inventory & Offers</CardTitle>
            <CardDescription>From signals to closed transactions</CardDescription>
          </CardHeader>
          <CardContent className=\"text-sm text-muted-foreground\">
            Includes offer templates, outreach sequences, operation checklists, and KPI scorecards.
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className=\"flex items-center gap-2 text-lg\"><Globe2 className=\"h-5 w-5 text-primary\" /> Promotion & Sharing</CardTitle>
            <CardDescription>Landing-ready public structure</CardDescription>
          </CardHeader>
          <CardContent className=\"text-sm text-muted-foreground\">
            Publicly accessible folder and assets for publishing, sharing, and business development.
          </CardContent>
        </Card>
      </section>

      <section>
        <h2 className=\"text-xl font-semibold mb-4\">Documents & Assets</h2>
        <div className=\"grid grid-cols-1 md:grid-cols-2 gap-4\">
          {docs.map((doc) => (
            <Card key={doc.href}>
              <CardContent className=\"pt-6 space-y-3\">
                <div className=\"flex items-start justify-between gap-4\">
                  <div>
                    <h3 className=\"font-semibold flex items-center gap-2\">
                      <FileText className=\"h-4 w-4 text-primary\" />
                      {doc.label}
                    </h3>
                    <p className=\"text-sm text-muted-foreground\">{doc.note}</p>
                  </div>
                </div>
                <Button asChild variant=\"outline\" className=\"gap-2\">
                  <a href={doc.href} target=\"_blank\" rel=\"noreferrer\">
                    Open
                    <ArrowUpRight className=\"h-4 w-4\" />
                  </a>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
"""

    write_text(target_repo / "src" / "components" / "ingtrade" / "IngTradePromoBlock.tsx", promo_component)
    write_text(target_repo / "src" / "pages" / "IngTradeLandingPage.tsx", landing_page)


def create_public_bundle(target_repo: Path) -> list[str]:
    out_root = target_repo / "public" / "ing-trade" / "business-kit"
    out_root.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []

    tree_sources = [
        (SOURCE_REPO / "used_equipment_business", out_root / "used_equipment_business"),
    ]

    for src, dst in tree_sources:
        if copy_tree(src, dst):
            copied.append(str(dst.relative_to(target_repo)))

    file_sources = [
        (SOURCE_REPO / "research" / "ingecart" / "machine_trading_company_view.csv", out_root / "intelligence" / "machine_trading_company_view.csv"),
        (SOURCE_REPO / "research" / "ingecart" / "machine_trading_company_view.md", out_root / "intelligence" / "machine_trading_company_view.md"),
        (SOURCE_REPO / "reports" / "Ing_TRADE_Business_Presentation.pptx", out_root / "sales_assets" / "Ing_TRADE_Business_Presentation.pptx"),
        (SOURCE_REPO / "reports" / "Ing_TRADE_Business_Presentation - version 2.pptx", out_root / "sales_assets" / "Ing_TRADE_Business_Presentation - version 2.pptx"),
        (SOURCE_REPO / "reports" / "templates" / "ING_TRADE_Presentation_Template.potx", out_root / "sales_assets" / "templates" / "ING_TRADE_Presentation_Template.potx"),
        (SOURCE_REPO / "reports" / "templates" / "ING_TRADE_Presentation_Template - version 2.potx", out_root / "sales_assets" / "templates" / "ING_TRADE_Presentation_Template - version 2.potx"),
        (SOURCE_REPO / "reports" / "templates" / "ING_TRADE_Offer_Template.docx", out_root / "sales_assets" / "templates" / "ING_TRADE_Offer_Template.docx"),
        (SOURCE_REPO / "reports" / "templates" / "ING_TRADE_Offer_Template - version 2.docx", out_root / "sales_assets" / "templates" / "ING_TRADE_Offer_Template - version 2.docx"),
        (SOURCE_REPO / "scripts" / "generate_ing_trade_documents.py", out_root / "automation" / "generate_ing_trade_documents.py"),
        (SOURCE_REPO / "reports" / "business_partner_report.md", out_root / "business_partner_report.md"),
    ]

    for src, dst in file_sources:
        if copy_file(src, dst):
            copied.append(str(dst.relative_to(target_repo)))

    readme = """# Ing_TRADE Business Kit

This folder bundles operational and commercial assets for launching and scaling the Ing_TRADE used machinery business.

## Included
- Used-equipment operating workspace (`used_equipment_business/`)
- Machine trading intelligence views (`intelligence/`)
- Commercial presentation and templates (`sales_assets/`)
- Reproducible generation script (`automation/`)

## Recommended Immediate Actions
1. Publish landing links for partner onboarding and inbound lead capture.
2. Reuse offer templates for first pilot deals.
3. Track weekly scorecard and iterate channel quality.
"""
    write_text(out_root / "README.md", readme)
    copied.append(str((out_root / "README.md").relative_to(target_repo)))

    manifest_path = target_repo / "public" / "ing-trade" / "manifest.json"
    write_text(
        manifest_path,
        json.dumps(
            {
                "bundle": "ing-trade",
                "version": "1.0.0",
                "source_repo": str(SOURCE_REPO),
                "copied_items": sorted(copied),
            },
            indent=2,
            ensure_ascii=False,
        ) + "\n",
    )
    copied.append(str(manifest_path.relative_to(target_repo)))

    return sorted(copied)


def deploy(target_repo: Path) -> None:
    if not target_repo.exists() or not target_repo.is_dir():
        raise FileNotFoundError(f"Target repository not found: {target_repo}")

    required = [
        target_repo / "src" / "App.tsx",
        target_repo / "src" / "components" / "AppSidebar.tsx",
        target_repo / "src" / "pages" / "DashboardPage.tsx",
    ]
    for file_path in required:
        if not file_path.exists():
            raise FileNotFoundError(f"Required file missing in target repo: {file_path}")

    copied = create_public_bundle(target_repo)
    create_react_files(target_repo)
    patch_app_tsx(target_repo)
    patch_sidebar(target_repo)
    patch_dashboard(target_repo)

    print(f"Target repo: {target_repo}")
    print("Ing_TRADE site bundle deployed.")
    print("Copied/updated items:")
    for item in copied:
        print(f"- {item}")
    print("- src/components/ingtrade/IngTradePromoBlock.tsx")
    print("- src/pages/IngTradeLandingPage.tsx")
    print("- src/App.tsx (route added)")
    print("- src/components/AppSidebar.tsx (navigation link added)")
    print("- src/pages/DashboardPage.tsx (promo block added)")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python deploy_ing_trade_site_bundle.py <target_repo_path>")
        sys.exit(1)

    target_repo = Path(sys.argv[1]).expanduser().resolve()
    deploy(target_repo)


if __name__ == "__main__":
    main()
