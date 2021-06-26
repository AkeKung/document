from __future__ import print_function
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint
from flask_restful import Resource
import os

class SendEmail(Resource):
    @classmethod
    def send_reset_email(cls,user,url):
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = os.getenv('API_KEY')

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
        subject = "Password Reset Request for LISA"

        html_content = """
        <!DOCTYPE html>
        <html>

        <head>
            <!-- Remote style sheet -->
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css">

        </head>

        <body style="background-color:#f9f9f9;">
            <div class= "container" style="background-color:#f9f9f9;width:500px;border-collapse:collapse;border-spacing:0;position:absolute;margin-left:auto;margin-right:auto;left:0;right:0;">
                <img src="https://firebasestorage.googleapis.com/v0/b/projectdoc-5af7b.appspot.com/o/template%2Fwp2570965.jpg?alt=media&token=678c9c38-92da-4ba1-ad89-32a461871e9e" style="height:auto;display:block;display: block;margin-left: auto;margin-right: auto;width: 100%;" </img>
                <table role="presentation" style="background-color:#ffffff;border: 1px solid #c5cad9;">
                    <tr>
                        <td style="text-align:center;vertical-align:top;direction:ltr;font-size:0px;padding:40px 50px">
                            <div aria-labelledby="mj-column-per-100" class="m_6964446768198031751mj-column-per-100"
                                style="vertical-align:top;display:inline-block;direction:ltr;font-size:13px;text-align:left;width:100%">
                                <table role="presentation" cellpadding="0" cellspacing="0" width="100%" border="0">
                                    <tbody>
                                        <tr>
                                            <td style="word-break:break-word;font-size:0px;padding:0px" align="left">
                                                <div
                                                    style="color:#737f8d;font-family:Whitney,Helvetica Neue,Helvetica,Arial,Lucida Grande,sans-serif;font-size:16px;line-height:24px;text-align:left">

                                                    <h2
                                                        style="font-family:Whitney,Helvetica Neue,Helvetica,Arial,Lucida Grande,sans-serif;font-weight:500;font-size:20px;color:#4f545c;letter-spacing:0.27px">
                                                        Hey {},</h2>
                                                    <p>Your LISA password can be <span class="il">reset</span> by clicking
                                                        the button below. If you did not request a new password, please ignore
                                                        this email.</p>

                                                </div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="word-break:break-word;font-size:0px;padding:10px 25px;padding-top:20px"
                                                align="center">
                                                <table role="presentation" cellpadding="0" cellspacing="0"
                                                    style="border-collapse:separate" align="center" border="0">
                                                    <tbody>
                                                        <tr>
                                                            <td style="border:none;border-radius:3px;color:white;padding:15px 19px"
                                                                align="center" valign="middle" bgcolor="#7289DA"><a
                                                                    href={}
                                                                    style="text-decoration:none;line-height:100%;background:#7289da;color:white;font-family:Ubuntu,Helvetica,Arial,sans-serif;font-size:15px;font-weight:normal;text-transform:none;margin:0px"
                                                                    <span class="il">Reset</span> Password
                                                                </a></td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="word-break:break-word;font-size:0px;padding:30px 0px">
                                                <p
                                                    style="font-size:1px;margin:0px auto;border-top:1px solid #dcddde;width:100%">
                                                </p>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="word-break:break-word;font-size:0px;padding:0px" align="left">
                                                <!-- <div
                                                    style="color:#747f8d;font-family:Whitney,Helvetica Neue,Helvetica,Arial,Lucida Grande,sans-serif;font-size:13px;line-height:16px;text-align:left">
                                                    <p>Need help? <a
                                                            href="https://url9624.discordapp.com/ls/click?upn=qDOo8cnwIoKzt0aLL1cBeNlOcN7VC1Mue2BSa5oqYEdKm-2BPBEvWHLEUfi61TfqfxuvBipSaAkPtkAVPOEnBIzw-3D-3DioHW_av9jLgVz1hP-2FL23lkyqaU7Iw5z8d9cjUxeAc64zG-2BCrkrwGzXJ0UvMvbPbh0CuPQR4XvzIFXgeoDwXnAKuYf1dtVLmy9bjZvmioy7CiEqaaUw0gzmeeN8hENSyy-2BFnnQe-2Bt0mXQLXh3CpZv7j24L7dUFCGxoOSGlsSi-2B4h5FzeuZMsnKz6Jpe5b264knMhKDgyD4eh8tObF3gzgwNSZy4OPjH7x6In-2B1V3zD3HFxLZI-3D"
                                                            style="font-family:Whitney,Helvetica Neue,Helvetica,Arial,Lucida Grande,sans-serif;color:#7289da"
                                                            target="_blank"
                                                            data-saferedirecturl="https://www.google.com/url?q=https://url9624.discordapp.com/ls/click?upn%3DqDOo8cnwIoKzt0aLL1cBeNlOcN7VC1Mue2BSa5oqYEdKm-2BPBEvWHLEUfi61TfqfxuvBipSaAkPtkAVPOEnBIzw-3D-3DioHW_av9jLgVz1hP-2FL23lkyqaU7Iw5z8d9cjUxeAc64zG-2BCrkrwGzXJ0UvMvbPbh0CuPQR4XvzIFXgeoDwXnAKuYf1dtVLmy9bjZvmioy7CiEqaaUw0gzmeeN8hENSyy-2BFnnQe-2Bt0mXQLXh3CpZv7j24L7dUFCGxoOSGlsSi-2B4h5FzeuZMsnKz6Jpe5b264knMhKDgyD4eh8tObF3gzgwNSZy4OPjH7x6In-2B1V3zD3HFxLZI-3D&amp;source=gmail&amp;ust=1623380898827000&amp;usg=AFQjCNGTsQC5Fqab-gw8xvqCTjY7INY4eA">Contact
                                                            our support team</a> or hit us up on Twitter <a
                                                            href="https://url9624.discordapp.com/ls/click?upn=qDOo8cnwIoKzt0aLL1cBeHLasbud5D3vi74o1Q-2B2VLcLLCDOodJpEqop-2Fc-2F5Wr6ZjdI4_av9jLgVz1hP-2FL23lkyqaU7Iw5z8d9cjUxeAc64zG-2BCrkrwGzXJ0UvMvbPbh0CuPQmfNZNY-2FILyobSO4P9h1dKzHEtVSzIVSf2C6VBGN9DjSQYjtAdAKazZ96BSDYTVd3xqazrmIvyMKeCNzgcESsWdgmr0II3ec6aUMcbe0EHYlcExYTWEjv-2Fm-2FHt1jtoP5r0dgiLOP-2BxY5cgnjSI0L2QbvlT3yhOgAtnVJhqAcw8a4-3D"
                                                            style="font-family:Whitney,Helvetica Neue,Helvetica,Arial,Lucida Grande,sans-serif;color:#7289da"
                                                            target="_blank"
                                                            data-saferedirecturl="https://www.google.com/url?q=https://url9624.discordapp.com/ls/click?upn%3DqDOo8cnwIoKzt0aLL1cBeHLasbud5D3vi74o1Q-2B2VLcLLCDOodJpEqop-2Fc-2F5Wr6ZjdI4_av9jLgVz1hP-2FL23lkyqaU7Iw5z8d9cjUxeAc64zG-2BCrkrwGzXJ0UvMvbPbh0CuPQmfNZNY-2FILyobSO4P9h1dKzHEtVSzIVSf2C6VBGN9DjSQYjtAdAKazZ96BSDYTVd3xqazrmIvyMKeCNzgcESsWdgmr0II3ec6aUMcbe0EHYlcExYTWEjv-2Fm-2FHt1jtoP5r0dgiLOP-2BxY5cgnjSI0L2QbvlT3yhOgAtnVJhqAcw8a4-3D&amp;source=gmail&amp;ust=1623380898827000&amp;usg=AFQjCNGqElMrsFM6MXSTUB1UeAxFcDL82A">@discord</a>.<br>
                                                        Want to give us feedback? Let us know what you think on our <a
                                                            href="https://url9624.discordapp.com/ls/click?upn=qDOo8cnwIoKzt0aLL1cBeGtifxhyb-2FEeTgeN31uAkBS2ZTvlNepPcLUnXgSC4-2BGKDJZ5_av9jLgVz1hP-2FL23lkyqaU7Iw5z8d9cjUxeAc64zG-2BCrkrwGzXJ0UvMvbPbh0CuPQ6TPLy9Qw8RLDdQqa-2FGwL6WJ8SBN1HwsACYgJU0ZE50Kkvc-2FIGtT3tspc5SN4pHdHBIV8MtzgM-2BrnV3KjlcRIWn4vrC8B-2B9ksewMuGYtz4X6GydIKgiWPWq5422hkh0NSDjiMtG6Oeczuo8aO2aeOHslFx7hJ8Xw-2FoHl-2Bo9RvsZ0-3D"
                                                            style="font-family:Whitney,Helvetica Neue,Helvetica,Arial,Lucida Grande,sans-serif;color:#7289da"
                                                            target="_blank"
                                                            data-saferedirecturl="https://www.google.com/url?q=https://url9624.discordapp.com/ls/click?upn%3DqDOo8cnwIoKzt0aLL1cBeGtifxhyb-2FEeTgeN31uAkBS2ZTvlNepPcLUnXgSC4-2BGKDJZ5_av9jLgVz1hP-2FL23lkyqaU7Iw5z8d9cjUxeAc64zG-2BCrkrwGzXJ0UvMvbPbh0CuPQ6TPLy9Qw8RLDdQqa-2FGwL6WJ8SBN1HwsACYgJU0ZE50Kkvc-2FIGtT3tspc5SN4pHdHBIV8MtzgM-2BrnV3KjlcRIWn4vrC8B-2B9ksewMuGYtz4X6GydIKgiWPWq5422hkh0NSDjiMtG6Oeczuo8aO2aeOHslFx7hJ8Xw-2FoHl-2Bo9RvsZ0-3D&amp;source=gmail&amp;ust=1623380898827000&amp;usg=AFQjCNGGgA4WPpC4yOpWcZL5KCJP9Tw_3w">feedback
                                                            site</a>.</p>

                                                </div> -->
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
        </body>

        </html>
        """.format(user.username,url)

        sender = {"name":"ADMIN_LISA","email":'noreply@lisaapp.com'}
        to = [{"email":user.email,"name":user.username}]
        #reply_to = {"email":'noreply@lisaapp.com',"name":'ADMIN_LISA'}#{"email":"replyto@domain.com","name":"John Doe"}
        headers = {"Some-Custom-Name":"unique-id-1234"}
        params = {"parameter":"My param value","subject":"New Subject"}
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to, headers=headers, html_content=html_content, sender=sender, subject=subject)

        try:
            api_response = api_instance.send_transac_email(send_smtp_email)
            pprint(api_response)
        except ApiException as e:
            print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)
