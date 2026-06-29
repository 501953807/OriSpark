"""DMCA 通知模板服务 (P2.3.7).

根据作品信息和侵权监测结果生成预填的 DMCA Takedown Notice.
"""

from datetime import datetime, timezone
from typing import Optional


DMCA_TEMPLATE_EN = """DMCA TAKEDOWN NOTICE

Date: {date}

To: {platform_name} Designated Copyright Agent

Re: Notice of Copyright Infringement Pursuant to 17 U.S.C. § 512(c)

1. IDENTIFICATION OF COPYRIGHTED WORK

The copyrighted work that has been infringed is:

    Title: {work_title}
    Author/Creator: {creator_name}
    Original URL: {original_url}
    Registration Number (if applicable): {registration_number}
    Date of Creation: {creation_date}

Description of the work:
{work_description}

2. IDENTIFICATION OF INFRINGING MATERIAL

The material that is claimed to be infringing is located at:

    URL: {infringing_url}
    Title/Description: {infringing_title}
    Discovered on: {discovery_date}

The following material is infringing on the exclusive rights of the copyright owner:
{infringing_description}

3. CONTACT INFORMATION OF COMPLAINING PARTY

    Name: {contact_name}
    Organization: {contact_organization}
    Address: {contact_address}
    Email: {contact_email}
    Phone: {contact_phone}

4. GOOD FAITH BELIEF STATEMENT

I have a good faith belief that the use of the copyrighted materials described
above as allegedly infringing is not authorized by the copyright owner, its
agent, or the law. I have taken fair use into consideration.

5. ACCURACY STATEMENT

I swear, under penalty of perjury, that the information in this notification is
accurate and that I am the copyright owner, or am authorized to act on behalf of
the owner, of an exclusive right that is allegedly infringed.

6. SIGNATURE

    Electronic Signature: ___________________________
    Printed Name: {contact_name}
    Date: {date}

---

IMPORTANT: This is a legally binding document. Please ensure all information is
accurate before sending. You may wish to consult with an attorney before
submitting this takedown notice.

The Digital Millennium Copyright Act (DMCA) provides a safe harbor for online
service providers (OSPs) that comply with the notice-and-takedown provisions.
However, submitting a false DMCA notice may result in liability for damages,
including costs and attorneys' fees under 17 U.S.C. § 512(f).
"""


def fill_dmca_template(
    work_title: str = "My Original Work",
    creator_name: str = "[Your Name / Company Name]",
    original_url: str = "[URL where your work is published]",
    registration_number: str = "N/A (Unregistered works are still protected)",
    creation_date: str = "[Date of creation, e.g., 2024-01-15]",
    work_description: str = "[Detailed description of your original work: "
                          "type of work (photograph, illustration, music, "
                          "software, etc.), key features, and any distinctive "
                          "elements that appear in the infringing copy.]",
    platform_name: str = "[Platform Name, e.g., Taobao, Amazon, Google]",
    infringing_url: str = "[URL of the infringing content]",
    infringing_title: str = "[Title of the infringing content]",
    discovery_date: str = "",
    infringing_description: str = "[Describe how the infringing material "
                                  "copies your original work. Be specific: "
                                  "identical reproduction, derivative work, "
                                  "unauthorized distribution, etc.]",
    contact_name: str = "[Your Full Name]",
    contact_organization: str = "[Your Company/Studio Name]",
    contact_address: str = "[Your Mailing Address]",
    contact_email: str = "[Your Email Address]",
    contact_phone: str = "[Your Phone Number]",
) -> str:
    """填充 DMCA 通知模板.

    Args:
        work_title: 原作品标题
        creator_name: 创作者/版权所有者名称
        original_url: 原作品 URL
        registration_number: 版权登记号 (可选)
        creation_date: 创作日期
        work_description: 作品描述
        platform_name: 侵权平台名称
        infringing_url: 侵权内容 URL
        infringing_title: 侵权内容标题
        discovery_date: 发现时间
        infringing_description: 侵权行为描述
        contact_name: 联系人姓名
        contact_organization: 联系组织
        contact_address: 联系地址
        contact_email: 联系邮箱
        contact_phone: 联系电话

    Returns:
        填充后的 DMCA 通知文本.
    """
    if not discovery_date:
        discovery_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return DMCA_TEMPLATE_EN.format(
        date=date,
        work_title=work_title,
        creator_name=creator_name,
        original_url=original_url,
        registration_number=registration_number,
        creation_date=creation_date,
        work_description=work_description,
        platform_name=platform_name,
        infringing_url=infringing_url,
        infringing_title=infringing_title,
        discovery_date=discovery_date,
        infringing_description=infringing_description,
        contact_name=contact_name,
        contact_organization=contact_organization,
        contact_address=contact_address,
        contact_email=contact_email,
        contact_phone=contact_phone,
    )


def fill_dmca_template_from_work(
    work_title: str,
    creator_name: str = "[Your Name]",
    original_url: str = "",
    infringing_url: str = "[Infringing URL]",
    infringing_title: str = "",
    contact_email: str = "[Your Email]",
) -> str:
    """从作品信息快速填充 DMCA 模板 (简化版).

    用于 GET /api/monitor/evidence/dmca/{work_id} 端点.
    """
    return fill_dmca_template(
        work_title=work_title,
        creator_name=creator_name,
        original_url=original_url or f"[Original publication URL for '{work_title}']",
        creation_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        work_description=f"[Describe your original work '{work_title}']",
        infringing_url=infringing_url,
        infringing_title=infringing_title or f"[Infringing copy of '{work_title}']",
        discovery_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        infringing_description=f"The infringing material appears to be an unauthorized reproduction of the original work '{work_title}'.",
        contact_name=creator_name,
        contact_email=contact_email,
    )
